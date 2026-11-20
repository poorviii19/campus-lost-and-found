"""
CampusCoin – thin re-export so context_processors can import CoinWallet cleanly.
"""
from .models import CoinWallet, CoinTransaction, CampusVendor

__all__ = ['CoinWallet', 'CoinTransaction', 'CampusVendor']
