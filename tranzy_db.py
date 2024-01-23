"""
SQLAlchemy ORM classes definitions for the tranzy database tables
"""

from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, Integer, Float, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Trip(Base):
    """
    Table with the monitored trips. A trip is one of the two directions of a route;
    trip_id is route_id suffixed by "_0" for main direction, and "_1" for return trip.
    """
    __tablename__ = "trip"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True)  # db auto id
    agency_id: Mapped[int] = mapped_column(Integer)
    route_id: Mapped[int] = mapped_column(Integer)
    trip_id: Mapped[str] = mapped_column(String)
    shape_id: Mapped[str] = mapped_column(String)
    route_short_name: Mapped[str] = mapped_column(String)
    route_long_name: Mapped[str] = mapped_column(String)
    trip_headsign: Mapped[str] = mapped_column(String)
    monitored: Mapped[bool] = mapped_column(Boolean)

    positions: Mapped["Position"] = relationship(back_populates="trip")
    trip_stops: Mapped["StopOrder"] = relationship(back_populates="trip")
    monitored_stops: Mapped["MonitoredStops"] = relationship(back_populates="trip")

    def __repr__(self):
        return f"Trip(idx={self.idx}, agency_id={self.agency_id}, " \
               f"trip_id={self.trip_id}, " \
               f"route_long_name={self.route_long_name}, " \
               f"trip_headsign={self.trip_headsign})"


class Position(Base):
    """
    Vehicle positions for the monitored trips.
    """
    __tablename__ = "position"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True)  # db auto id
    vehicle_no: Mapped[str] = mapped_column(String)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    speed: Mapped[int] = mapped_column(Integer)
    stop_distance: Mapped[int] = mapped_column(Integer)
    trip_idx = mapped_column(ForeignKey("trip.idx"))  # PK in trip table (not tranzy trip_id)
    stop_idx = mapped_column(ForeignKey("stop.idx"))

    trip: Mapped["Trip"] = relationship(back_populates="positions")
    closest_stop: Mapped["Stop"] = relationship(back_populates="positions")

    def __repr__(self):
        return f"Position(vehicle_no={self.vehicle_no}, " \
               f"latitude={self.latitude}, " \
               f"longitude={self.longitude}, " \
               f"timestamp={self.timestamp}, " \
               f"trip_idx={self.trip_idx})"


class Stop(Base):
    """
    Table with all the stops of the monitored trips.
    """
    __tablename__ = "stop"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True)  # db auto id
    stop_id: Mapped[int] = mapped_column(Integer)
    stop_name: Mapped[str] = mapped_column(String)
    stop_lat: Mapped[float] = mapped_column(Float)
    stop_lon: Mapped[float] = mapped_column(Float)

    stops_order: Mapped["StopOrder"] = relationship(back_populates="stop")
    positions: Mapped["Position"] = relationship(back_populates="closest_stop")

    def __repr__(self):
        return f"Stop(idx={self.idx},stop_id={self.stop_id}, stop_name={self.stop_name})"


class StopOrder(Base):
    """
    Table with the stops order for each monitored trip.
    """
    __tablename__ = "stop_order"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True)  # db auto id
    stop_order: Mapped[int] = mapped_column(Integer)
    trip_idx = mapped_column(ForeignKey("trip.idx"))
    stop_idx = mapped_column(ForeignKey("stop.idx"))  # PK in stop table (not tranzy stop_id)

    trip: Mapped[Trip] = relationship(back_populates="trip_stops")
    stop: Mapped[Stop] = relationship(back_populates="stops_order")

    def __repr__(self):
        return f"StopOrder(stop_order={self.stop_order}, stop_idx={self.stop_idx})"


class MonitoredStops(Base):
    """
    Table with the stops to monitor, by defining a start and end stop
    """
    __tablename__ = "monitored_stops"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True)  # db auto id
    start_stop: Mapped[int] = mapped_column(Integer)
    end_stop: Mapped[int] = mapped_column(Integer)
    trip_idx = mapped_column(ForeignKey("trip.idx"))

    trip: Mapped[Trip] = relationship(back_populates="monitored_stops")

    def __repr__(self):
        return f"MonitoredStop(start={self.start_stop}, end={self.end_stop}), trip_idx={self.trip_idx}"
