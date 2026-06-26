from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import Bill, SessionLocal, create_tables, engine # Assuming models.py is in the project root

# Create tables if they don't exist. In a real app, this should be handled by migrations.
# create_tables()

router = APIRouter(
    prefix="/bills",
    tags=["bills"]
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=Bill)
def create_bill(bill: Bill, db: Session = Depends(get_db)):
    # Note: The 'bill' object here is expected to be Pydantic-validated, not a SQLAlchemy model instance directly.
    # We need to convert it or accept data and create the model instance.
    # For simplicity, let's assume 'bill' data is passed and we create the model.
    db_bill = Bill(
        name=bill.name, 
        amount=bill.amount, 
        due_date=bill.due_date, 
        recurrence=bill.recurrence, 
        user_id=bill.user_id # Assuming user_id is provided
    )
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)
    return db_bill

@router.get("/", response_model=List[Bill])
def read_bills(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    bills = db.query(Bill).offset(skip).limit(limit).all()
    return bills

@router.get("/{bill_id}", response_model=Bill)
def read_bill(bill_id: int, db: Session = Depends(get_db)):
    db_bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if db_bill is None:
        raise HTTPException(status_code=404, detail="Bill not found")
    return db_bill

@router.put("/{bill_id}", response_model=Bill)
def update_bill(bill_id: int, bill_update: Bill, db: Session = Depends(get_db)):
    db_bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if db_bill is None:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    # Update fields
    db_bill.name = bill_update.name
    db_bill.amount = bill_update.amount
    db_bill.due_date = bill_update.due_date
    db_bill.recurrence = bill_update.recurrence
    db_bill.user_id = bill_update.user_id
    
    db.commit()
    db.refresh(db_bill)
    return db_bill

@router.delete("/{bill_id}", response_model=Bill)
def delete_bill(bill_id: int, db: Session = Depends(get_db)):
    db_bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if db_bill is None:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    db.delete(db_bill)
    db.commit()
    return db_bill
