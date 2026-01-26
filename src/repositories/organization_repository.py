from sqlalchemy.orm import Session
from models.organization import Organization

class OrganizationRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_name(self, name: str) -> Organization | None:
        """名前で事業部を取得"""
        return self.db.query(Organization).filter(Organization.name == name).first()
    
    def get_all(self) -> list[Organization]:
        """全事業部を取得"""
        return self.db.query(Organization).order_by(Organization.name).all()
