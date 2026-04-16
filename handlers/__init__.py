from handlers.menu import router as menu_router
from handlers.learn import router as learn_router
from handlers.games import router as games_router
from handlers.multiplayer import router as multiplayer_router
from handlers.stats import router as stats_router

all_routers = [
    menu_router,
    learn_router,
    games_router,
    multiplayer_router,
    stats_router,
]