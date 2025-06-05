from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# Import models from their individual files
from app.models.user import User
from app.models.game import Game
from app.models.move import Move
from app.models.player import Player

# This file serves as a central reference for all models
# All models are defined in their individual files in the models/ directory