"""
Service layer untuk Rule Engine — auto-categorization.
"""
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models import Category, Rule, Transaction
from ..schemas.rule import RuleCreate, RuleUpdate

WIB = timezone(__import__("datetime").timedelta(hours=7))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _rule_to_response(rule: Rule) -> dict:
    return {
        "id": rule.id,
        "name": rule.name,
        "match_keywords": rule.match_keywords,
        "category_id": rule.category_id,
        "category_name": rule.category.name if rule.category else None,
        "category_icon": rule.category.icon if rule.category else None,
        "category_color": rule.category.color if rule.category else None,
        "match_mode": rule.match_mode,
        "is_active": bool(rule.is_active),
        "priority": rule.priority,
        "match_count": rule.match_count,
        "last_matched_at": rule.last_matched_at,
        "created_at": rule.created_at,
        "updated_at": rule.updated_at,
    }


async def list_rules(db: AsyncSession, user_id: int) -> list[dict]:
    result = await db.execute(
        select(Rule)
        .options(joinedload(Rule.category))
        .where(Rule.user_id == user_id)
        .order_by(Rule.priority.desc(), Rule.id.asc())
    )
    return [_rule_to_response(r) for r in result.unique().scalars().all()]


async def create_rule(db: AsyncSession, user_id: int, data: RuleCreate) -> dict:
    # Validate category
    cat = await db.execute(
        select(Category).where(Category.id == data.category_id, Category.is_active == 1)
    )
    if not cat.scalar_one_or_none():
        raise HTTPException(status_code=422, detail={
            "status": "error", "message": "Kategori tidak ditemukan",
            "errors": {"category_id": ["Invalid"]}
        })

    rule = Rule(
        user_id=user_id,
        name=data.name,
        match_keywords=data.match_keywords,
        category_id=data.category_id,
        match_mode=data.match_mode,
        priority=data.priority,
    )
    db.add(rule)
    await db.flush()
    await db.refresh(rule, ["category"])
    return _rule_to_response(rule)


async def update_rule(db: AsyncSession, rule_id: int, user_id: int, data: RuleUpdate) -> dict:
    result = await db.execute(
        select(Rule).options(joinedload(Rule.category)).where(Rule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule or rule.user_id != user_id:
        raise HTTPException(status_code=404, detail={
            "status": "error", "message": "Rule tidak ditemukan"
        })

    updates = data.model_dump(exclude_unset=True)
    for key, val in updates.items():
        if key == "is_active":
            setattr(rule, key, 1 if val else 0)
            continue
        setattr(rule, key, val)

    await db.flush()
    await db.refresh(rule, ["category"])
    return _rule_to_response(rule)


async def delete_rule(db: AsyncSession, rule_id: int, user_id: int) -> None:
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule or rule.user_id != user_id:
        raise HTTPException(status_code=404, detail={
            "status": "error", "message": "Rule tidak ditemukan"
        })
    await db.delete(rule)
    await db.flush()


def _match_notes(notes: str, keywords: str, mode: str) -> bool:
    """Check if notes match keywords based on mode."""
    if not notes or not keywords:
        return False
    notes_lower = notes.lower()
    for keyword in keywords.split(","):
        trimmed = keyword.strip().lower()
        if not trimmed:
            continue
        if mode == "exact":
            if notes_lower == trimmed:
                return True
        elif mode == "startswith":
            if notes_lower.startswith(trimmed):
                return True
        elif trimmed in notes_lower:  # contains (default)
            return True
    return False


async def apply_rules_to_transaction(
    db: AsyncSession, user_id: int, transaction: Transaction
) -> int | None:
    """Apply matching rules to a transaction. Returns category_id if matched, else None."""
    if not transaction.notes:
        return None

    # Get active rules, ordered by priority desc
    result = await db.execute(
        select(Rule)
        .where(Rule.user_id == user_id, Rule.is_active == 1)
        .order_by(Rule.priority.desc(), Rule.id.asc())
    )
    rules = result.scalars().all()

    for rule in rules:
        if _match_notes(transaction.notes, rule.match_keywords, rule.match_mode):
            # Update rule stats
            if rule:
                rule.match_count = (rule.match_count or 0) + 1
                rule.last_matched_at = _now_utc()
                await db.flush()
                return int(rule.category_id)

    return None


async def apply_rules_to_existing(
    db: AsyncSession, user_id: int, days: int = 30
) -> dict:
    """Re-run rules on existing uncategorized transactions."""
    from datetime import timedelta
    cutoff = datetime.now(WIB).date() - timedelta(days=days)

    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.category_id.is_(None),
            Transaction.transaction_date >= cutoff,
        ).order_by(Transaction.transaction_date.desc())
    )
    transactions = result.scalars().all()

    updated = 0
    for tx in transactions:
        cat_id = await apply_rules_to_transaction(db, user_id, tx)
        if cat_id:
            tx.category_id = cat_id
            updated += 1

    await db.flush()
    return {"total_checked": len(transactions), "updated": updated}
