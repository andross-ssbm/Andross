# Use an official Python 3.10 runtime as a parent image
FROM python:3.10-slim-buster

# Set timezone to discord servers timezone
ENV TZ=America/New_York

# Install prerequisites
RUN apt-get update
RUN apt-get install -y git cron vim

# Set working directory
WORKDIR /Andross/Andross

# Copy all files in current directory to image
COPY . .

# Update pip and install required dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/Andross
ENV DISCORD_COMMAND_PREFIX=$

RUN mv entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["start"]
