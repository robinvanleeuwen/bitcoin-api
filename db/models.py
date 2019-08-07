from sqlalchemy import *
from sqlalchemy.orm import relationship

from db import db


class Ticker(db.Model):

    __tablename__ = "ticker"
    __table_args__ = (
        Index('timestamp_idx', 'timestamp', unique=False),
    )

    id = Column(Integer, primary_key=True)

    pair = Column(CHAR(7))

    a_price = Column(Numeric(18, 5))
    a_whole_lot_volume = Column(Numeric(18, 8))
    a_lot_volume = Column(Numeric(18, 8))

    b_price = Column(Numeric(18, 5))
    b_whole_lot_volume = Column(Numeric(18, 8))
    b_lot_volume = Column(Numeric(18, 8))

    c_price = Column(Numeric(18, 5))
    c_lot_volume = Column(Numeric(18, 8))

    v_today = Column(Numeric(18, 8))
    v_24_hours = Column(Numeric(18, 8))

    p_today = Column(Numeric(18, 5))
    p_24_hours = Column(Numeric(18, 5))

    t_today = Column(Integer)
    t_24_hours = Column(Integer)

    l_today = Column(Numeric(18, 5))
    l_24_hours = Column(Numeric(18, 5))

    h_today = Column(Numeric(18, 5))
    h_24_hours = Column(Numeric(18, 5))

    o_today = Column(Numeric(18, 5))
    o_24_hours = Column(Numeric(18, 5))

    timestamp = Column(Numeric(18, 5))


class Ohlc(db.Model):

    __tablename__ = "ohlc"
    __table_args__ = (
        Index("idx_interval_endtime", "interval", "begintime", unique=True),
    )

    id = Column(Integer, primary_key=True)
    pair = Column(CHAR(7))
    interval = Column(Integer())
    time = Column(Numeric(18, 4))
    begintime = Column(Numeric(18, 4))
    endtime = Column(Numeric(18, 4))
    open = Column(Numeric(18, 8))
    high = Column(Numeric(18, 8))
    low = Column(Numeric(18, 8))
    close = Column(Numeric(18, 8))
    vwap = Column(Numeric(18, 8))
    count = Column(Numeric(18, 8))


class Users(db.Model):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_name", "name"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    password = Column(Text)


class Tokens(db.Model):

    __tablename__ = "tokens"
    __table_args__ = (
        Index("idx_token", "token"),
    )

    id = Column(Integer(), primary_key=True)
    token = Column(Text(), unique=True)
    user_id = Column(Integer(), ForeignKey("users.id"))
    timestamp = Column(DateTime())
    ttl_max = Column(DateTime())
    ttl_increment = Column(Integer())
    last_ip_address = Column(Text())

    user = relationship("Users", foreign_keys=[user_id])
