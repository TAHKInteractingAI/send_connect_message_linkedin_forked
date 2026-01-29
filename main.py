# from fastapi import FastAPI, BackgroundTasks
# import uvicorn
# from copy_of_connect_linkedin_with_cookie import main_connect
# #from copy_of_message_linkedin_with_cookie import main_mess
# app = FastAPI()

# @app.post("/run-connect")
# async def run_connect_api(background_tasks: BackgroundTasks):
#     """API Endpoint trả về ngay lập tức cho Cron-job"""
#     background_tasks.add_task(main_connect)
#     return {
#         "message": "Script has started in background",
#         "status": "processing"
#     }

# # @app.post("/run-mess")
# # async def run_mess_api(background_tasks: BackgroundTasks):
# #     """API Endpoint trả về ngay lập tức cho Cron-job"""
# #     background_tasks.add_task(main_mess)
# #     return {
# #         "message": "Script has started in background",
# #         "status": "processing"
# #     }

# @app.get("/")
# def home():
#     return {"status": "Server is running"}

# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=True)