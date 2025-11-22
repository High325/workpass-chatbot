"""
Knowledge base module for Singapore Work Pass Chatbot
"""
from .scraper import MOMScraper
from .processor import DataProcessor
from .builder import KnowledgeBaseBuilder

__all__ = ['MOMScraper', 'DataProcessor', 'KnowledgeBaseBuilder']


