from sqlalchemy import select,func
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.models import Skill,UserSkill,Swap
from app.exceptions import BusinessRuleError,ConflictError,NotFoundError
from app.services import user_service

def get_or_404(sid,s=None):
    own=s is None; s=s or SessionLocal(); x=s.get(Skill,sid)
    if own:s.close()
    if not x: raise NotFoundError(f"Skill {sid} not found")
    return x

def out(x): return {"id":x.id,"name":x.name,"category":x.category,"description":x.description}
def create_skill(data):
    with SessionLocal() as s:
        if s.scalar(select(Skill).where(func.lower(Skill.name)==data.name.lower())): raise ConflictError(f"Skill '{data.name}' already exists")
        x=Skill(name=data.name,category=data.category.value,description=data.description);s.add(x)
        try:s.commit()
        except IntegrityError:s.rollback();raise ConflictError(f"Skill '{data.name}' already exists")
        s.refresh(x);return out(x)
def list_skills(category,search):
    with SessionLocal() as s:
        q=select(Skill).order_by(Skill.id)
        if category:q=q.where(Skill.category==category.value)
        if search:q=q.where(func.lower(Skill.name).contains(search.lower()))
        return [out(x) for x in s.scalars(q)]
def get_skill(sid):
    with SessionLocal() as s:
        x=s.get(Skill,sid)
        if not x:raise NotFoundError(f"Skill {sid} not found")
        return out(x)
def update_skill(sid,data):
    with SessionLocal() as s:
        x=s.get(Skill,sid)
        if not x:raise NotFoundError(f"Skill {sid} not found")
        c={k:v for k,v in data.model_dump(exclude_unset=True).items() if v is not None or k=="description"}
        if not c:raise BusinessRuleError("No fields provided for update")
        if "name" in c:
            c["name"]=c["name"]
            if s.scalar(select(Skill).where(func.lower(Skill.name)==c["name"].lower(),Skill.id!=sid)):raise ConflictError(f"Skill '{c['name']}' already exists")
        for k,v in c.items():setattr(x,k,v.value if hasattr(v,"value") else v)
        s.commit();s.refresh(x);return out(x)
def delete_skill(sid):
    with SessionLocal() as s:
        x=s.get(Skill,sid)
        if not x:raise NotFoundError(f"Skill {sid} not found")
        used=s.scalar(select(UserSkill.id).where(UserSkill.skill_id==sid).limit(1)) or s.scalar(select(Swap.id).where((Swap.skill_id==sid)|(Swap.offered_skill_id==sid)).limit(1))
        if used:raise ConflictError("Skill is used in profiles or swaps and cannot be deleted")
        s.delete(x);s.commit()
def list_teachers(sid):
    with SessionLocal() as s:
        if not s.get(Skill,sid):raise NotFoundError(f"Skill {sid} not found")
        rows=s.execute(select(UserSkill,UserSkill.user_id).where(UserSkill.skill_id==sid,UserSkill.kind=="offer")).all()
        result=[]
        for r,_ in rows:
            u=s.get(type(r.user),r.user_id) if False else r.user
            result.append({**user_service.serialize(u,s),"teaching_level":r.level})
        return sorted(result,key=lambda t:(-(t["average_rating"] or 0),t["id"]))
