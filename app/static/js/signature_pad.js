// SignaturePad.js
(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
    typeof define === 'function' && define.amd ? define(factory) :
    (global = global || self, global.SignaturePad = factory());
}(this, function () {
    'use strict';

    var SignaturePad = (function () {
        function SignaturePad(canvas, options) {
            var _this = this;
            this.canvas = canvas;
            this.options = options || {};
            this._ctx = canvas.getContext('2d');
            this._mouseButtonDown = false;
            this._lastPoints = [];
            this._data = [];
            this._lastVelocity = 0;
            this._lastWidth = (this.options.minWidth + this.options.maxWidth) / 2;
            this._strokeMoveUpdate = this._strokeUpdate.bind(this);
            this.velocityFilterWeight = this.options.velocityFilterWeight || 0.7;
            this.minWidth = this.options.minWidth || 0.5;
            this.maxWidth = this.options.maxWidth || 2.5;
            this.throttle = this.options.throttle || 16;
            this.minDistance = this.options.minDistance || 1;
            this.dotSize = this.options.dotSize || function () {
                return (_this.minWidth + _this.maxWidth) / 2;
            };
            this.penColor = this.options.penColor || 'black';
            this.backgroundColor = this.options.backgroundColor || 'rgba(0,0,0,0)';
            this._ctx.lineCap = 'round';
            this._ctx.lineJoin = 'round';
            this._clear();
            this._handleMouseEvents();
            this._handleTouchEvents();
            this.resizeCanvas();
        }

        SignaturePad.prototype.clear = function () {
            this._data = [];
            this._clear();
            this._reset();
        };

        SignaturePad.prototype.fromData = function (pointGroups) {
            var _this = this;
            this.clear();
            this._fromData(pointGroups, function (curve, widths) {
                _this._drawCurve(curve, widths.start, widths.end);
            }, function (rawPoint) {
                return _this._drawDot(rawPoint);
            });
        };

        SignaturePad.prototype.toData = function () {
            return this._data;
        };

        SignaturePad.prototype.toDataURL = function (type, encoderOptions) {
            return this.canvas.toDataURL(type, encoderOptions);
        };

        SignaturePad.prototype.onBegin = function (event) {
            this._data.push([]);
            this._reset();
            this._strokeBegin(event);
        };

        SignaturePad.prototype.onEnd = function (event) {
            var _this = this;
            var data = this._data;
            var lastGroup = data[data.length - 1];
            if (lastGroup && lastGroup.length === 0) {
                data.pop();
            }
            this._strokeEnd(event);
        };

        SignaturePad.prototype._strokeBegin = function (event) {
            this._lastPoints = [];
            this._lastVelocity = 0;
            this._lastWidth = (this.minWidth + this.maxWidth) / 2;
            this._addPoint(this._createPoint(event));
        };

        SignaturePad.prototype._strokeEnd = function (event) {
            // Ne rien faire de spécial à la fin du trait
        };

        SignaturePad.prototype._strokeUpdate = function (event) {
            var point = this._createPoint(event);
            this._addPoint(point);
            if (this._lastPoints.length >= 2) {
                this._drawCurve(this._lastPoints.slice(-2), this._lastWidth, this._lastWidth);
            }
            this._lastPoints.push(point);
            this._lastWidth = this._strokeWidthUpdate(this._lastVelocity);
            this._lastVelocity = this._strokeVelocityUpdate(point);
        };

        SignaturePad.prototype._handleMouseEvents = function () {
            var _this = this;
            this.mouseButtonDown = false;
            this.canvas.addEventListener('mousedown', function (event) {
                if (event.which === 1) {
                    _this.mouseButtonDown = true;
                    _this.onBegin(event);
                }
            });
            this.canvas.addEventListener('mousemove', function (event) {
                if (_this.mouseButtonDown) {
                    _this._strokeMoveUpdate(event);
                }
            });
            document.addEventListener('mouseup', function (event) {
                if (_this.mouseButtonDown && event.which === 1) {
                    _this.mouseButtonDown = false;
                    _this.onEnd(event);
                }
            });
            this.canvas.addEventListener('mouseout', function (event) {
                if (_this.mouseButtonDown) {
                    _this.mouseButtonDown = false;
                    _this.onEnd(event);
                }
            });
        };

        SignaturePad.prototype._handleTouchEvents = function () {
            var _this = this;
            this.canvas.addEventListener('touchstart', function (event) {
                if (event.targetTouches.length === 1) {
                    var touch = event.targetTouches[0];
                    _this.onBegin(touch);
                }
            });
            this.canvas.addEventListener('touchmove', function (event) {
                var touch = event.targetTouches[0];
                _this._strokeMoveUpdate(touch);
                event.preventDefault();
            });
            document.addEventListener('touchend', function (event) {
                var wasCanvasTouched = event.target === _this.canvas;
                if (wasCanvasTouched) {
                    _this.onEnd(event);
                }
            });
        };

        SignaturePad.prototype.resizeCanvas = function () {
            var ratio = Math.max(window.devicePixelRatio || 1, 1);
            this.canvas.width = this.canvas.offsetWidth * ratio;
            this.canvas.height = this.canvas.offsetHeight * ratio;
            this.canvas.getContext('2d').scale(ratio, ratio);
            this._ctx = this.canvas.getContext('2d');
            this._ctx.lineCap = 'round';
            this._ctx.lineJoin = 'round';
            this._clear();
        };

        SignaturePad.prototype._clear = function () {
            this._ctx.fillStyle = this.backgroundColor;
            this._ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this._ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        };

        SignaturePad.prototype._reset = function () {
            this._lastPoints = [];
            this._lastVelocity = 0;
            this._lastWidth = (this.minWidth + this.maxWidth) / 2;
            this._ctx.fillStyle = this.penColor;
        };

        SignaturePad.prototype._createPoint = function (event) {
            var rect = this.canvas.getBoundingClientRect();
            return new Point(event.clientX - rect.left, event.clientY - rect.top);
        };

        SignaturePad.prototype._strokeWidthUpdate = function (velocity) {
            return Math.max(this.maxWidth / (velocity + 1), this.minWidth);
        };

        SignaturePad.prototype._strokeVelocityUpdate = function (point) {
            var lastPoints = this._lastPoints;
            var lastPoint = lastPoints[lastPoints.length - 1];
            var pointVelocity = lastPoint ? point.distanceFrom(lastPoint) / (Date.now() - lastPoint.time) : 0;
            return this.velocityFilterWeight * pointVelocity + (1 - this.velocityFilterWeight) * this._lastVelocity;
        };

        SignaturePad.prototype._addPoint = function (point) {
            var lastGroup = this._data[this._data.length - 1];
            lastGroup.push({
                x: point.x,
                y: point.y,
                time: Date.now(),
                color: this.penColor
            });
        };

        SignaturePad.prototype._drawCurve = function (points, startWidth, endWidth) {
            if (points.length < 2) return;
            
            var ctx = this._ctx;
            var widthDelta = endWidth - startWidth;
            var drawSteps = Math.floor(points.length / 2);
            
            ctx.beginPath();
            ctx.fillStyle = this.penColor;
            
            for (var i = 0; i < drawSteps; i += 1) {
                var width = startWidth + (widthDelta * i / drawSteps) | 0;
                var point = points[i];
                var nextPoint = points[i + 1];
                
                if (!point || !nextPoint) continue;
                
                ctx.moveTo(point.x, point.y);
                ctx.lineTo(nextPoint.x, nextPoint.y);
                ctx.lineWidth = width;
                ctx.stroke();
            }
            
            ctx.closePath();
        };

        SignaturePad.prototype._drawDot = function (point) {
            var ctx = this._ctx;
            var width = typeof this.dotSize === 'function' ? this.dotSize() : this.dotSize;
            ctx.beginPath();
            ctx.arc(point.x, point.y, width, 0, 2 * Math.PI, false);
            ctx.fillStyle = this.penColor;
            ctx.fill();
        };

        SignaturePad.prototype._fromData = function (pointGroups, drawCurve, drawDot) {
            var _this = this;
            for (var i = 0; i < pointGroups.length; i += 1) {
                var group = pointGroups[i];
                var points = group.points;
                if (points.length > 1) {
                    for (var j = 0; j < points.length; j += 1) {
                        var basicPoint = points[j];
                        var point = new Point(basicPoint.x, basicPoint.y, basicPoint.time);
                        this._lastPoints.push(point);
                        if (j === 0) {
                            this._reset();
                        }
                        if (j === points.length - 1) {
                            this._drawCurve([{ point: point }], this._lastWidth, this._lastWidth);
                            this._lastPoints = [];
                        }
                    }
                }
                else {
                    this._reset();
                    drawDot(points[0]);
                    this._lastPoints = [];
                }
            }
        };

        SignaturePad.prototype.isEmpty = function () {
            return this._data.length === 0 || this._data.every(function (group) {
                return group.length === 0;
            });
        };

        return SignaturePad;
    }());

    var Point = (function () {
        function Point(x, y, time) {
            this.x = x;
            this.y = y;
            this.time = time || Date.now();
        }

        Point.prototype.distanceFrom = function (start) {
            return Math.sqrt(Math.pow(this.x - start.x, 2) + Math.pow(this.y - start.y, 2));
        };

        Point.prototype.velocityFrom = function (start) {
            return this.time !== start.time ? this.distanceFrom(start) / (this.time - start.time) : 0;
        };

        return Point;
    }());

    return SignaturePad;
})); 