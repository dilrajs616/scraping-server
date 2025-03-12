from quart import Quart, request, jsonify, Response
from scripts.categorizing.llama3_classification import categorize
from scripts.scraping.scrape import scrape_all_websites
import asyncio
import json
import os

app = Quart(__name__)

request_queue = asyncio.Queue()

@app.before_serving
async def startup():
    """ Start the request processor when the app starts. """
    asyncio.create_task(process_requests())

async def process_requests():
    """ Process requests sequentially from the queue. """
    while True:
        request_data, response_future = await request_queue.get()
        response_generator = await handle_request(request_data)
        response_future.set_result(response_generator)  # Send generator back to waiting request
        request_queue.task_done()

async def save_content(record_id, content):
    """ Saves the scraped content in the appropriate directory. """
    base_dir = "data"
    
    # Determine folder paths based on record_id
    folder_100k = os.path.join(base_dir, str((record_id // 100000) * 100000))
    folder_10k = os.path.join(folder_100k, str((record_id // 10000) * 10000))
    folder_1k = os.path.join(folder_10k, str((record_id // 1000) * 1000))
    
    # Ensure folders exist
    os.makedirs(folder_1k, exist_ok=True)
    
    # Save content in file
    file_path = os.path.join(folder_1k, f"{record_id}.txt")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

async def handle_request(request_data):
    """ Processes the request and returns a response generator. """
    domains_dict = request_data["domains"]
    domain_list = list(domains_dict.keys())

    async def generate_results():
        async for result in scrape_all_websites(domain_list, max_tabs=10):
            record_id = domains_dict.get(result["site"])

            if result['content']:
                categorized_data = categorize(result['site'], result['content'])
                response_data = {
                    "site": result['site'],
                    "final_url": result['final_url'],
                    "language": result['language'],
                    "country": result['country'],
                    "sub_domain": result['sub_domain'],
                    "domain": result['domain'],
                    "categorized": categorized_data
                }

                # Save content in appropriate directory
                await save_content(record_id, result['content'])

            else:
                response_data = {
                    "site": result['site'],
                    "message": f"Unable to scrape URL: {result['site']}"
                }

            yield f"{json.dumps({'data': response_data})}\n\n"

    return generate_results

@app.route("/scrape-categorize", methods=['POST'])
async def enqueue_request():
    """ Add request to queue and wait for the response generator. """
    try:
        data = await request.get_json()

        if 'domains' not in data or not isinstance(data['domains'], dict):
            return jsonify({"error": "Invalid input, 'domains' should be a dictionary"}), 400

        response_future = asyncio.Future()
        await request_queue.put((data, response_future))

        # Wait for response generator
        response_generator = await response_future
        return Response(response_generator(), mimetype="text/event-stream")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
