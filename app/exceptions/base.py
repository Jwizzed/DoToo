from fastapi import HTTPException, status

# Common Exceptions
CredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

InactiveUserException = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Inactive user",
)

PermissionDeniedException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Not enough permissions",
)

NotFoundException = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found",
)

BadRequestException = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Bad request",
)

DuplicateEntryException = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Duplicate entry",
)

FileUploadException = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="File upload failed",
)
