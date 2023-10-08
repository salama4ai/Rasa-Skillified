# Use the official Rasa SDK base image
FROM rasa/rasa-sdk:3.5.1

WORKDIR  /app

USER root

COPY . .
# Expose the Rasa Action Server port
EXPOSE 5055

# Set the entrypoint command to run the Rasa Action Server
CMD ["start", "--actions", "actions"]