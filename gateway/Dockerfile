FROM rust:1.82-slim AS build
WORKDIR /app
COPY Cargo.toml .
COPY src/ src/
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /app/target/release/apv-gateway /usr/local/bin/apv-gateway
EXPOSE 8080
CMD ["apv-gateway"]
