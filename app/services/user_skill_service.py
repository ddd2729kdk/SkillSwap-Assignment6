from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.models import User,Skill,UserSkill,Swap
from app.exceptions import BusinessRuleError,ConflictError,NotFoundError
ACTIVE=("pending","accepted")
def out(r):return {"id":r.id,"user_id":r.user_id,"skill_id":r.skill_id,"skill_name":r.skill.name,"kind":r.kind,"level":r.level,"note":r.note}
def add_user_skill(uid,data):
    with SessionLocal() as s:
        if not s.get(User,uid):raise NotFoundError(f"User {uid} not found")
        skill=s.get(Skill,data.skill_id)
        if not skill:raise NotFoundError(f"Skill {data.skill_id} not found")
        old=s.scalar(select(UserSkill).where(UserSkill.user_id==uid,UserSkill.skill_id==data.skill_id))
        if old:raise ConflictError(f"This skill is already in the profile as '{old.kind}'; remove it first")
        r=UserSkill(user_id=uid,skill_id=data.skill_id,kind=data.kind.value,level=data.level.value,note=data.note);s.add(r)
        try:s.commit()
        except IntegrityError:s.rollback();raise ConflictError("This skill is already in the profile")
        s.refresh(r);return out(r)
def list_user_skills(uid,kind):
    with SessionLocal() as s:
        if not s.get(User,uid):raise NotFoundError(f"User {uid} not found")
        q=select(UserSkill).where(UserSkill.user_id==uid).order_by(UserSkill.id)
        if kind:q=q.where(UserSkill.kind==kind.value)
        return [out(r) for r in s.scalars(q)]
def update_user_skill(uid,rid,data):
    with SessionLocal() as s:
        if not s.get(User,uid):raise NotFoundError(f"User {uid} not found")
        r=s.scalar(select(UserSkill).where(UserSkill.id==rid,UserSkill.user_id==uid))
        if not r:raise NotFoundError(f"Skill entry {rid} not found for user {uid}")
        c=data.model_dump(exclude_unset=True)
        if not c:raise BusinessRuleError("No fields provided for update")
        for k,v in c.items():setattr(r,k,v.value if hasattr(v,"value") else v)
        s.commit();s.refresh(r);return out(r)
def remove_user_skill(uid,rid):
    with SessionLocal() as s:
        if not s.get(User,uid):raise NotFoundError(f"User {uid} not found")
        r=s.scalar(select(UserSkill).where(UserSkill.id==rid,UserSkill.user_id==uid))
        if not r:raise NotFoundError(f"Skill entry {rid} not found for user {uid}")
        if r.kind=="offer":
            active=s.scalar(select(Swap.id).where(Swap.status.in_(ACTIVE),((Swap.partner_id==uid)&(Swap.skill_id==r.skill_id))|((Swap.requester_id==uid)&(Swap.offered_skill_id==r.skill_id))).limit(1))
            if active:raise ConflictError("Skill is used in a pending or accepted swap and cannot be removed")
        s.delete(r);s.commit()
