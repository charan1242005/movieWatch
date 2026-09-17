import os,re,html as htmlmod
from datetime import datetime,timedelta,timezone
import httpx
from fastapi import FastAPI,Depends,HTTPException,Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm,HTTPBearer,HTTPAuthorizationCredentials
from pydantic import BaseModel,EmailStr
from sqlalchemy import create_engine,Column,Integer,String,DateTime,ForeignKey,Boolean,Enum as SAEnum
from sqlalchemy.orm import declarative_base,sessionmaker,Session,relationship
from jose import jwt,JWTError
from passlib.context import CryptContext

DATABASE_URL=os.getenv('DATABASE_URL','sqlite:///./moviewatch.db')
JWT_SECRET=os.getenv('JWT_SECRET','change-me')
CORS_ORIGINS=[x.strip() for x in os.getenv('CORS_ORIGINS','*').split(',') if x.strip()]
engine=create_engine(DATABASE_URL,connect_args={'check_same_thread':False} if DATABASE_URL.startswith('sqlite') else {})
SessionLocal=sessionmaker(bind=engine,autocommit=False,autoflush=False)
Base=declarative_base(); pwd=CryptContext(schemes=['bcrypt'],deprecated='auto'); bearer=HTTPBearer(auto_error=False)
class User(Base):
 __tablename__='users'; id=Column(Integer,primary_key=True); name=Column(String,nullable=False); email=Column(String,unique=True,index=True,nullable=False); hashed_password=Column(String,nullable=False); telegram_chat_id=Column(String); notify_email=Column(String); created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc)); trackers=relationship('Tracker',back_populates='user',cascade='all, delete-orphan')
class Movie(Base):
 __tablename__='movies'; id=Column(Integer,primary_key=True); title=Column(String,nullable=False,index=True); external_id=Column(String); language=Column(String); poster_url=Column(String); created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Tracker(Base):
 __tablename__='trackers'; id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey('users.id'),nullable=False); movie_id=Column(Integer,ForeignKey('movies.id'),nullable=False); city=Column(String,nullable=False); date=Column(String,nullable=False); platform=Column(SAEnum('BOOKMYSHOW','DISTRICT','BOTH','MOCK',name='Platform',create_type=False),nullable=False,default='MOCK'); cinema=Column(String,default='Any Cinema'); language=Column(String); format=Column(String); start_time=Column(String); end_time=Column(String); seats_required=Column(Integer,default=1); adjacent_seats=Column(Boolean,default=False); status=Column(SAEnum('ACTIVE','STOPPED','FULFILLED',name='TrackerStatus',create_type=False),nullable=False,default='STOPPED'); check_interval=Column(Integer,default=5); last_checked_at=Column(DateTime(timezone=True)); created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc)); updated_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc)); user=relationship('User',back_populates='trackers'); movie=relationship('Movie'); shows=relationship('Show',back_populates='tracker',cascade='all, delete-orphan'); notifications=relationship('Notification',back_populates='tracker',cascade='all, delete-orphan')
class Show(Base):
 __tablename__='shows'; id=Column(Integer,primary_key=True); tracker_id=Column(Integer,ForeignKey('trackers.id'),nullable=False); provider=Column(String,nullable=False); cinema=Column(String,nullable=False); screen=Column(String); show_time=Column(String,nullable=False); available_seats=Column(Integer,default=0); adjacent_available=Column(Boolean); booking_url=Column(String); last_seen_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc)); tracker=relationship('Tracker',back_populates='shows')
class Notification(Base):
 __tablename__='notifications'; id=Column(Integer,primary_key=True); tracker_id=Column(Integer,ForeignKey('trackers.id'),nullable=False); notification_type=Column(String,nullable=False); message=Column(String,nullable=False); sent_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc)); status=Column(String,default='sent'); tracker=relationship('Tracker',back_populates='notifications')

class RegisterIn(BaseModel): name:str; email:EmailStr; password:str
class UserOut(BaseModel):
 id:int; name:str; email:EmailStr; telegram_chat_id:str|None=None; notify_email:EmailStr|None=None; created_at:datetime
 model_config={'from_attributes':True}
class Token(BaseModel): access_token:str; token_type:str='bearer'
class SettingsIn(BaseModel): telegram_chat_id:str|None=None; notify_email:EmailStr|None=None
class TrackerIn(BaseModel): movie_title:str; city:str; date:str; platform:str='mock'; cinema:str='Any Cinema'; language:str|None=None; format:str|None=None; start_time:str|None=None; end_time:str|None=None; seats_required:int=1; adjacent_seats:bool=False; check_interval:int=5
class TrackerOut(BaseModel): id:int; user_id:int; movie_id:int; movie_title:str|None=None; city:str; date:str; platform:str; cinema:str; language:str|None=None; format:str|None=None; start_time:str|None=None; end_time:str|None=None; seats_required:int; adjacent_seats:bool; status:str; check_interval:int; last_checked_at:datetime|None=None; created_at:datetime; updated_at:datetime
class ShowOut(BaseModel): id:int; tracker_id:int; provider:str; cinema:str; screen:str|None=None; show_time:str; available_seats:int; adjacent_available:bool|None=None; booking_url:str|None=None; last_seen_at:datetime
class MovieOut(BaseModel): id:int; title:str; external_id:str|None=None; language:str|None=None; poster_url:str|None=None
class NotificationOut(BaseModel): id:int; tracker_id:int; notification_type:str; message:str; sent_at:datetime; status:str

app=FastAPI(title='MovieWatch API',version='1.0.0'); app.add_middleware(CORSMiddleware,allow_origins=CORS_ORIGINS if CORS_ORIGINS!=['*'] else ['*'],allow_credentials=CORS_ORIGINS!=['*'],allow_methods=['*'],allow_headers=['*'])
def db():
 s=SessionLocal()
 try: yield s
 finally:s.close()
def auth(creds:HTTPAuthorizationCredentials=Depends(bearer),s:Session=Depends(db)):
 if not creds: raise HTTPException(401,'Not authenticated')
 try: uid=int(jwt.decode(creds.credentials,JWT_SECRET,algorithms=['HS256']).get('sub'))
 except (JWTError,TypeError,ValueError): raise HTTPException(401,'Invalid token')
 u=s.get(User,uid)
 if not u: raise HTTPException(401,'User not found')
 return u
def tracker_out(t): return TrackerOut(id=t.id,user_id=t.user_id,movie_id=t.movie_id,movie_title=t.movie.title if t.movie else None,city=t.city,date=t.date,platform=str(t.platform).lower(),cinema=t.cinema,language=t.language,format=t.format,start_time=t.start_time,end_time=t.end_time,seats_required=t.seats_required,adjacent_seats=t.adjacent_seats,status=str(t.status).lower(),check_interval=t.check_interval,last_checked_at=t.last_checked_at,created_at=t.created_at,updated_at=t.updated_at)
@app.on_event('startup')
def startup(): Base.metadata.create_all(engine)
@app.get('/health')
def health(): return {'status':'ok','service':'moviewatch'}
@app.post('/api/auth/register',response_model=UserOut,status_code=201)
def register(x:RegisterIn,s:Session=Depends(db)):
 if s.query(User).filter(User.email==x.email).first(): raise HTTPException(400,'Email already registered')
 u=User(name=x.name,email=x.email,hashed_password=pwd.hash(x.password)); s.add(u); s.commit(); s.refresh(u); return u
@app.post('/api/auth/login',response_model=Token)
def login(f:OAuth2PasswordRequestForm=Depends(),s:Session=Depends(db)):
 u=s.query(User).filter(User.email==f.username).first()
 if not u or not pwd.verify(f.password,u.hashed_password): raise HTTPException(401,'Incorrect email or password')
 return Token(access_token=jwt.encode({'sub':str(u.id),'exp':datetime.now(timezone.utc)+timedelta(days=1)},JWT_SECRET,algorithm='HS256'))
@app.get('/api/auth/me',response_model=UserOut)
def me(u=Depends(auth)): return u
@app.put('/api/auth/me/settings',response_model=UserOut)
def settings(x:SettingsIn,u=Depends(auth),s:Session=Depends(db)):
 if x.telegram_chat_id is not None:u.telegram_chat_id=x.telegram_chat_id
 if x.notify_email is not None:u.notify_email=x.notify_email
 s.commit();s.refresh(u);return u

def city_slug(platform,city):
 c=re.sub(r'[^a-z0-9]+','-',city.lower()).strip('-')
 if platform=='bookmyshow': return 'vizag-visakhapatnam' if c in ('vizag','visakhapatnam','visakhapatnam-ap') else c
 return 'vizag' if c in ('vizag','visakhapatnam') else c
def booking_url(platform,city,movie=''):
 if platform=='bookmyshow': return f'https://in.bookmyshow.com/explore/movies-{city_slug(platform,city)}'
 return f'https://www.district.in/movies/{city_slug(platform,city)}-movie-tickets'
async def public_movies(q,city,platform):
 base='https://in.bookmyshow.com' if platform=='bookmyshow' else 'https://www.district.in'; path=f'/explore/home/{city_slug(platform,city)}' if platform=='bookmyshow' else f'/movies/{city_slug(platform,city)}-movie-tickets'
 try:
  async with httpx.AsyncClient(timeout=12,headers={'User-Agent':'MovieWatch/1.0 (public-page monitor)'}) as c:r=await c.get(base+path); text=htmlmod.unescape(re.sub('<[^>]+>',' ',r.text))
  if r.status_code in (401,403,429) or re.search(r'captcha|verify you are human|unusual traffic|access denied',text,re.I): return []
  if q.lower() in text.lower(): return [MovieOut(id=0,title=q,external_id=q)]
 except Exception: pass
 return []
@app.get('/api/movies/search',response_model=list[MovieOut])
async def search_movies(q:str=Query(...,min_length=1),city:str='',platform:str='mock'):
 if platform=='mock': return [MovieOut(id=0,title=q,external_id=q)]
 return await public_movies(q,city,platform)
async def check_public(t:Tracker):
 movie=t.movie.title if t.movie else ''; found=[]
 for p in ([t.platform] if t.platform!='BOTH' else ['BOOKMYSHOW','DISTRICT']):
  base='https://in.bookmyshow.com' if p=='BOOKMYSHOW' else 'https://www.district.in'; slug=city_slug(p,t.city); path=f'/explore/home/{slug}' if p=='BOOKMYSHOW' else f'/movies/{slug}-movie-tickets'
  try:
   async with httpx.AsyncClient(timeout=15,headers={'User-Agent':'MovieWatch/1.0 (public-page monitor)'}) as c:r=await c.get(base+path)
   text=htmlmod.unescape(re.sub(r'<[^>]+>',' ',r.text))
   if r.status_code in (401,403,429) or re.search(r'captcha|verify you are human|unusual traffic|access denied|checking your browser',text,re.I): continue
   if movie and movie.lower() not in text.lower(): continue
   times=[]
   for m in re.findall(r'(?<!\d)(\d{1,2}[:.]\d{2}\s*(?:AM|PM)?)(?!\d)',text,re.I):
    tm=m.replace('.' ,':').upper().replace(' ','')
    if tm not in times: times.append(tm)
   for tm in times[:50]: found.append((p,'Public listing',tm,booking_url(p,t.city,movie)))
  except Exception: continue
 return found
async def do_check(t:Tracker,s:Session):
 results=[('MOCK','Demo Cinema','10:00 AM',booking_url('district',t.city,t.movie.title))] if t.platform=='MOCK' else await check_public(t)
 now=datetime.now(timezone.utc); existing={(x.provider,x.cinema,x.show_time):x for x in s.query(Show).filter(Show.tracker_id==t.id).all()}
 for p,cin,tm,url in results:
  row=existing.get((p,cin,tm)); was=bool(row and row.available_seats>=t.seats_required)
  if not row: row=Show(tracker_id=t.id,provider=p,cinema=cin,show_time=tm,available_seats=1,adjacent_available=True,booking_url=url); s.add(row)
  else: row.available_seats=1;row.last_seen_at=now;row.booking_url=url
  s.flush()
  if not was: s.add(Notification(tracker_id=t.id,notification_type='in_app',message=f'🎬 MOVIE TICKETS AVAILABLE!\n\nMovie: {t.movie.title}\nCinema: {cin}\nCity: {t.city}\nDate: {t.date}\nShowtime: {tm}\n\nBook now:\n{url}',status='sent'))
 t.last_checked_at=now;s.commit();return [x for x in s.query(Show).filter(Show.tracker_id==t.id).all()]
@app.get('/api/trackers',response_model=list[TrackerOut])
def list_trackers(u=Depends(auth),s:Session=Depends(db)): return [tracker_out(x) for x in s.query(Tracker).filter(Tracker.user_id==u.id).order_by(Tracker.id.desc()).all()]
@app.get('/api/trackers/{tid}',response_model=TrackerOut)
def get_tracker(tid:int,u=Depends(auth),s:Session=Depends(db)):
 t=s.query(Tracker).filter(Tracker.id==tid,Tracker.user_id==u.id).first()
 if not t:raise HTTPException(404,'Tracker not found')
 return tracker_out(t)
@app.post('/api/trackers',response_model=TrackerOut)
def create_tracker(x:TrackerIn,u=Depends(auth),s:Session=Depends(db)):
 m=s.query(Movie).filter(Movie.title.ilike(x.movie_title)).first() or Movie(title=x.movie_title,external_id=x.movie_title);s.add(m);s.flush();p=x.platform.upper();p=p if p in ('BOOKMYSHOW','DISTRICT','BOTH','MOCK') else 'MOCK'
 t=Tracker(user_id=u.id,movie_id=m.id,city=x.city,date=x.date,platform=p,cinema=x.cinema,language=x.language,format=x.format,start_time=x.start_time,end_time=x.end_time,seats_required=x.seats_required,adjacent_seats=x.adjacent_seats,check_interval=max(1,x.check_interval),status='STOPPED');s.add(t);s.commit();s.refresh(t);return tracker_out(t)
@app.put('/api/trackers/{tid}',response_model=TrackerOut)
def update_tracker(tid:int,x:dict,u=Depends(auth),s:Session=Depends(db)):
 t=s.query(Tracker).filter(Tracker.id==tid,Tracker.user_id==u.id).first()
 if not t:raise HTTPException(404,'Tracker not found')
 for k,v in x.items():
  if k=='platform':v=v.upper()
  if k!='movie_title' and hasattr(t,k):setattr(t,k,v)
 s.commit();s.refresh(t);return tracker_out(t)
@app.delete('/api/trackers/{tid}')
def delete_tracker(tid:int,u=Depends(auth),s:Session=Depends(db)):
 t=s.query(Tracker).filter(Tracker.id==tid,Tracker.user_id==u.id).first()
 if not t:raise HTTPException(404,'Tracker not found')
 s.delete(t);s.commit();return {'ok':True}
@app.post('/api/trackers/{tid}/start',response_model=TrackerOut)
async def start(tid:int,u=Depends(auth),s:Session=Depends(db)):
 t=s.query(Tracker).filter(Tracker.id==tid,Tracker.user_id==u.id).first()
 if not t:raise HTTPException(404,'Tracker not found')
 t.status='ACTIVE';s.commit();await do_check(t,s);s.refresh(t);return tracker_out(t)
@app.post('/api/trackers/{tid}/stop',response_model=TrackerOut)
def stop(tid:int,u=Depends(auth),s:Session=Depends(db)):
 t=s.query(Tracker).filter(Tracker.id==tid,Tracker.user_id==u.id).first()
 if not t:raise HTTPException(404,'Tracker not found')
 t.status='STOPPED';s.commit();s.refresh(t);return tracker_out(t)
@app.post('/api/trackers/{tid}/check',response_model=list[ShowOut])
async def check(tid:int,u=Depends(auth),s:Session=Depends(db)):
 t=s.query(Tracker).filter(Tracker.id==tid,Tracker.user_id==u.id).first()
 if not t:raise HTTPException(404,'Tracker not found')
 return await do_check(t,s)
@app.get('/api/trackers/{tid}/shows',response_model=list[ShowOut])
def shows(tid:int,u=Depends(auth),s:Session=Depends(db)):
 t=s.query(Tracker).filter(Tracker.id==tid,Tracker.user_id==u.id).first()
 if not t:raise HTTPException(404,'Tracker not found')
 return s.query(Show).filter(Show.tracker_id==tid).order_by(Show.show_time).all()
@app.get('/api/notifications',response_model=list[NotificationOut])
def notifications(u=Depends(auth),s:Session=Depends(db)):
 ids=[t.id for t in s.query(Tracker.id).filter(Tracker.user_id==u.id).all()];return s.query(Notification).filter(Notification.tracker_id.in_(ids)).order_by(Notification.id.desc()).limit(100).all() if ids else []
