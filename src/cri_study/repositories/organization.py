from sqlalchemy.orm import Session
from fastapi import Depends

from models.organization import Organization
from models.database import get_db


class OrganizationRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_name(self, name: str) -> Organization | None:
        """事業部名で事業部を取得"""
        return self.db.query(Organization).filter(Organization.name == name).first()
    
    def get_all(self) -> list[Organization]:
        """全事業部を取得"""
        return self.db.query(Organization).order_by(Organization.name).all()


def get_organization_repository(db: Session = Depends(get_db)) -> OrganizationRepository:
    return OrganizationRepository(db)
