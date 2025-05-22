class NotFoundException(Exception):
    """Exception levée lorsqu'une ressource n'est pas trouvée"""
    pass

class ValidationError(Exception):
    """Exception levée lors d'une erreur de validation"""
    pass

class AuthenticationError(Exception):
    """Exception levée lors d'une erreur d'authentification"""
    pass

class AuthorizationError(Exception):
    """Exception levée lors d'une erreur d'autorisation"""
    pass

class DatabaseError(Exception):
    """Exception levée lors d'une erreur de base de données"""
    pass

class BusinessLogicError(Exception):
    """Exception levée lors d'une erreur de logique métier"""
    pass 