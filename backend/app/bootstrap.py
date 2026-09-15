"""Inicialização explícita para desenvolvimento: python -m app.bootstrap."""
from getpass import getpass
from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import Base, Membership, User
from app.models.tenant import Tenant


def main():
    email = input("Email: ").strip().lower()
    name = input("Nome do tenant: ").strip()
    password = getpass("Senha (mínimo 12 caracteres): ")
    if not email or not name or not 12 <= len(password) <= 1024:
        raise SystemExit("Dados inválidos")
    with SessionLocal.begin() as db:
        if db.scalar(select(User).where(User.email == email)):
            raise SystemExit("Usuário já existe")
        user = User(email=email, password_hash=hash_password(password))
        tenant = Tenant(name=name)
        db.add_all([user, tenant])
        db.flush()
        db.add(Membership(user_id=user.id, tenant_id=tenant.id))
        tenant_id = tenant.id
    print(f"Tenant criado: {tenant_id}")


if __name__ == "__main__":
    main()
