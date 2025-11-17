# app/auth.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional

from app.schemas import User, UserCreate, UserRole, Token
from app.core.database import users_db # Import the shared users_db

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_user_from_token(token: str) -> Optional[User]:
    """Retrieves a user from the mock database using their username as a token."""
    # In a real application, this would decode a JWT token
    return users_db.get(token)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Dependency to get the currently authenticated user."""
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_recruiter_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get the currently authenticated user with recruiter role."""
    if current_user.role != UserRole.RECRUITER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized: Recruiter role required.")
    return current_user

async def get_current_candidate_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get the currently authenticated user with candidate role."""
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized: Candidate role required.")
    return current_user

@router.post("/register", response_model=User)
async def register_user(user_data: UserCreate):
    """Registers a new user (candidate or recruiter)."""
    if user_data.username in users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Default role to CANDIDATE if not specified in UserCreate (though our schema requires it)
    # Ensure role is explicitly set if not coming from UserCreate
    user_data_dict = user_data.model_dump()
    user_data_dict["id"] = str(uuid.uuid4())
    # UserCreate doesn't have a role, User does. We need to decide how role is set upon registration.
    # For now, let's assume `UserCreate` includes role, or we default it.
    # To simplify, I'll modify UserCreate schema in schemas.py to include role.
    
    new_user = User(**user_data_dict) 
    
    users_db[user_data.username] = new_user
    return new_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticates a user and returns an access token."""
    user = users_db.get(form_data.username)
    if not user or user.password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # In this mock setup, the access_token is just the username
    access_token = user.username
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Retrieves the profile of the currently authenticated user."""
    return current_user