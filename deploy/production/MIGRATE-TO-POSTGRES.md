# Di chuyển từ SQLite sang PostgreSQL

Tài liệu này áp dụng cho trường hợp đang chạy ArcReel bằng SQLite mặc định và muốn chuyển sang PostgreSQL.

## Điều kiện tiên quyết

- Đã cài Docker và Docker Compose
- ArcReel hiện đang chạy bằng SQLite (file cơ sở dữ liệu nằm tại `projects/.arcreel.db`)

## Các bước di chuyển

### 1. Dừng dịch vụ ArcReel

```bash
# Nếu chạy bằng Docker
docker compose down

# Nếu chạy trực tiếp bằng dòng lệnh, dừng tiến trình uvicorn
```

### 2. Sao lưu cơ sở dữ liệu SQLite

```bash
cp projects/.arcreel.db projects/.arcreel.db.bak
```

### 3. Cấu hình biến môi trường

Thêm biến sau vào `.env` (dùng để khởi tạo container PostgreSQL trong docker-compose):

```env
POSTGRES_PASSWORD=mat_khau_co_so_du_lieu_cua_ban
```

> Không cần đặt thủ công `DATABASE_URL`; giá trị đã được ghép tự động trong `docker-compose.yml` từ `POSTGRES_PASSWORD`.

### 4. Khởi động PostgreSQL

Trước tiên chỉ khởi động dịch vụ cơ sở dữ liệu:

```bash
docker compose up -d postgres
```

Đợi healthcheck thành công:

```bash
docker compose ps  # Xác nhận trạng thái postgres là healthy
```

### 5. Di chuyển dữ liệu

Dùng pgloader trong container ArcReel để chuyển trực tiếp dữ liệu từ SQLite sang PostgreSQL:

```bash
docker compose run --rm arcreel bash -c "
  apt-get update && apt-get install -y --no-install-recommends pgloader &&
  pgloader sqlite:///app/projects/.arcreel.db \
           postgresql://arcreel:\${POSTGRES_PASSWORD}@postgres:5432/arcreel
"
```

> pgloader sẽ tự xử lý khác biệt kiểu dữ liệu và cú pháp giữa SQLite và PostgreSQL (boolean, định dạng thời gian, ...),
> đồng thời bỏ qua schema đã tồn tại và chỉ nhập dữ liệu.

### 6. Xác minh dữ liệu

```bash
docker compose exec postgres psql -U arcreel -d arcreel -c "
  SELECT 'tasks' AS tbl, COUNT(*) FROM tasks
  UNION ALL
  SELECT 'api_calls', COUNT(*) FROM api_calls
  UNION ALL
  SELECT 'agent_sessions', COUNT(*) FROM agent_sessions
  UNION ALL
  SELECT 'api_keys', COUNT(*) FROM api_keys;
"
```

Đối chiếu số bản ghi trong SQLite:

```bash
sqlite3 projects/.arcreel.db "
  SELECT 'tasks', COUNT(*) FROM tasks
  UNION ALL
  SELECT 'api_calls', COUNT(*) FROM api_calls
  UNION ALL
  SELECT 'agent_sessions', COUNT(*) FROM agent_sessions
  UNION ALL
  SELECT 'api_keys', COUNT(*) FROM api_keys;
"
```

### 7. Khởi động toàn bộ dịch vụ

```bash
docker compose up -d
```

Truy cập `http://<IP_cua_ban>:1241` để xác nhận dịch vụ hoạt động bình thường.

---

## Quay lui về SQLite

Nếu cần quay lui:

1. Dừng dịch vụ: `docker compose down`
2. Khôi phục bản sao lưu: `cp projects/.arcreel.db.bak projects/.arcreel.db`
3. Xóa `POSTGRES_PASSWORD` trong `.env` và khởi động mà không dùng cấu hình PostgreSQL trong `docker-compose.yml`
