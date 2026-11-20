"""
Global context processors that inject data into every template.
"""
from .coin_models import CoinWallet  # re-exported from coin_models for clarity


def coin_balance(request):
    """
    Injects the logged-in user's CampusCoin balance into every template context.
    Non-authenticated users get balance = 0.
    """
    if request.user.is_authenticated:
        try:
            wallet = CoinWallet.get_or_create_wallet(request.user)
            return {
                'coin_balance': wallet.balance,
                'can_redeem_coins': wallet.can_redeem(),
            }
        except Exception:
            pass
    return {
        'coin_balance': 0,
        'can_redeem_coins': False,
    }
