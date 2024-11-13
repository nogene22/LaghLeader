# Use a Python base image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the bot code and .env file
COPY . .

# Run the bot
CMD ["python", "leader.py"]
