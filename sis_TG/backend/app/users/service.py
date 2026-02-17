import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.users.models import User, ROLE_LEVELS
from app.users.schemas import UserCreate, UserUpdate, UserUpdateMe
from app.auth.security import hash_password


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_users(self, current_user: User) -> list[User]:
        query = self.db.query(User)
        if current_user.role != "superadmin":
            allowed_roles = [
                r for r, level in ROLE_LEVELS.items()
                if level < current_user.role_level
            ]
            query = query.filter(User.role.in_(allowed_roles))
        return query.order_by(User.created_at.desc()).all()

    def get_user(self, user_id: uuid.UUID) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, data: UserCreate, current_user: User) -> User:
        target_level = ROLE_LEVELS.get(data.role, 0)
        if target_level >= current_user.role_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes crear un usuario con un rol igual o superior al tuyo",
            )

        existing = self.db.query(User).filter(User.email == data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya esta registrado",
            )

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
            created_by=current_user.id,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user_id: uuid.UUID, data: UserUpdate, current_user: User) -> User:
        user = self.get_user(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if user.role_level >= current_user.role_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes editar un usuario con rol igual o superior al tuyo",
            )

        if data.role is not None:
            target_level = ROLE_LEVELS.get(data.role, 0)
            if target_level >= current_user.role_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No puedes asignar un rol igual o superior al tuyo",
                )

        if data.email is not None:
            existing = self.db.query(User).filter(
                User.email == data.email, User.id != user_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="El email ya esta registrado")
            user.email = data.email

        if data.full_name is not None:
            user.full_name = data.full_name
        if data.role is not None:
            user.role = data.role
        if data.is_active is not None:
            user.is_active = data.is_active

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: uuid.UUID, current_user: User) -> None:
        user = self.get_user(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if user.role_level >= current_user.role_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes eliminar un usuario con rol igual o superior al tuyo",
            )

        user.is_active = False
        self.db.commit()

    def update_me(self, data: UserUpdateMe, current_user: User) -> User:
        if data.full_name is not None:
            current_user.full_name = data.full_name
        if data.password is not None:
            current_user.hashed_password = hash_password(data.password)
        self.db.commit()
        self.db.refresh(current_user)
        return current_user
