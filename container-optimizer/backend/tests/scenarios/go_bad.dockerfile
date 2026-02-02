FROM golang
RUN git clone https://github.com/someone/somerepo.git
WORKDIR /go/src/app
COPY . .
RUN go build -o main .
CMD ["./main"]
