from sqlalchemy import select
from app.database import SessionLocal
from app.models import User
from app.schemas.review import ReviewCreate
from app.schemas.skill import SkillCreate
from app.schemas.swap import SwapCreate,SwapStatus,SwapStatusUpdate
from app.schemas.user import UserCreate
from app.schemas.user_skill import UserSkillCreate
from app.services import review_service,skill_service,swap_service,user_service,user_skill_service
from datetime import datetime,timedelta,timezone
SKILLS=[("Python","programming"),("English","languages"),("Guitar","music"),("Graphic Design","design"),("Calculus","science"),("Public Speaking","business")]
USERS=[("Aigerim Sadykova","aigerim@satbayev.kz","Satbayev University","Software Engineering",2),("Daniyar Omarov","daniyar@satbayev.kz","Satbayev University","Information Systems",3),("Madina Kenzhebay","madina@kaznu.kz","Al-Farabi KazNU","Philology",2),("Alikhan Nurlanov","alikhan@kaznu.kz","Al-Farabi KazNU","Mathematics",4),("Zarina Beketova","zarina@kbtu.kz","KBTU","Design",1)]
PROFILES={1:{"offer":[(1,"advanced"),(5,"intermediate")],"want":[(2,"intermediate"),(3,"beginner")]},2:{"offer":[(3,"advanced"),(6,"intermediate")],"want":[(1,"beginner"),(4,"beginner")]},3:{"offer":[(2,"advanced"),(6,"advanced")],"want":[(1,"beginner"),(5,"beginner")]},4:{"offer":[(5,"advanced"),(1,"intermediate")],"want":[(2,"intermediate"),(6,"beginner")]},5:{"offer":[(4,"advanced"),(3,"beginner")],"want":[(1,"beginner"),(2,"beginner")]}}
def seed_data():
    with SessionLocal() as s:
        if s.scalar(select(User.id).limit(1)):return
    for n,c in SKILLS:skill_service.create_skill(SkillCreate(name=n,category=c))
    for name,email,uni,major,year in USERS:user_service.create_user(UserCreate(full_name=name,email=email,university=uni,major=major,year_of_study=year))
    for uid,groups in PROFILES.items():
        for kind,items in groups.items():
            for sid,level in items:user_skill_service.add_user_skill(uid,UserSkillCreate(skill_id=sid,kind=kind,level=level))
    sw=swap_service.create_swap(SwapCreate(requester_id=1,partner_id=3,skill_id=2,offered_skill_id=1,message="Let's practice English and Python together",scheduled_at=datetime.now(timezone.utc)+timedelta(days=3),duration_minutes=60))
    swap_service.change_status(sw["id"],SwapStatusUpdate(actor_id=3,status=SwapStatus.accepted))
    swap_service.change_status(sw["id"],SwapStatusUpdate(actor_id=1,status=SwapStatus.completed))
    review_service.create_review(ReviewCreate(swap_id=sw["id"],author_id=1,rating=5,comment="Great teacher"))
