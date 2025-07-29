from fastapi import FastAPI
from app.routes.trade_routes import router as trade_router
from app.websockets import start_websocket

import threading
import time
from app.strategies import ema_crossover_strategy

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Start WebSocket thread
    threading.Thread(target=start_websocket).start()

app.include_router(trade_router)



def run_strategy_periodically():
    while True:
        print("Running strategy...")
        ema_crossover_strategy.ema_crossover("INFY")
        time.sleep(300)  # Run every 5 minutes

@app.on_event("startup")
async def startup_event():
    # Start WebSocket connection
    from app.websockets import start_websocket
    start_websocket()

    # Start EMA Crossover strategy runner
    thread = threading.Thread(target=run_strategy_periodically)
    thread.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)