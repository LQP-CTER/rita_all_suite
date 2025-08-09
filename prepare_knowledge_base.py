# prepare_knowledge_base.py
import json
import faiss
import numpy as np
import csv  # Thư viện để đọc file CSV
from sentence_transformers import SentenceTransformer


def create_knowledge_base():
    """
    Hàm này đọc dữ liệu từ 2 nguồn:
    1. knowledge.txt: Chứa thông tin chung về dự án.
    2. Data.csv: Chứa thông tin về bạn bè của bạn.
    Sau đó, xử lý và tạo ra hai tệp "bộ não" cho AI.
    """
    print("Bắt đầu quá trình tạo cơ sở tri thức...")

    # 1. Tải mô hình embedding
    print("Đang tải mô hình SentenceTransformer...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Tải mô hình thành công.")

    # --- PHẦN MỚI: Đọc và xử lý Data.csv ---
    all_text_chunks = []
    try:
        with open('Data.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # Đọc dòng tiêu đề (ví dụ: Tên, Tuổi, Nghề nghiệp)

            print(f"Đang đọc Data.csv với các cột: {', '.join(header)}")

            for row in reader:
                # Với mỗi dòng, tạo một câu văn tự nhiên chứa thông tin
                # Ví dụ: "Đây là thông tin về [Tên]: Tuổi là [Tuổi], Nghề nghiệp là [Nghề nghiệp]."
                # BẠN CÓ THỂ TÙY CHỈNH CÁCH TẠO CÂU NÀY CHO PHÙ HỢP

                info_parts = []
                for i, value in enumerate(row):
                    if value.strip():  # Chỉ thêm thông tin nếu ô không rỗng
                        info_parts.append(f"{header[i]} là {value}")

                if info_parts:
                    # Ghép các mẩu thông tin lại thành một câu hoàn chỉnh
                    full_sentence = f"Thông tin về {row[0]}: " + ", ".join(info_parts[1:]) + "."
                    all_text_chunks.append(full_sentence)

        print(f"Đã xử lý thành công {len(all_text_chunks)} dòng thông tin từ Data.csv.")

    except FileNotFoundError:
        print("CẢNH BÁO: Không tìm thấy tệp 'Data.csv'. Bỏ qua nguồn dữ liệu này.")
    except Exception as e:
        print(f"LỖI khi đọc Data.csv: {e}")

    # --- Đọc tệp knowledge.txt (giữ nguyên) ---
    try:
        with open('knowledge.txt', 'r', encoding='utf-8') as f:
            knowledge_txt_chunks = [line.strip() for line in f if line.strip()]
            all_text_chunks.extend(knowledge_txt_chunks)
            print(f"Đã thêm {len(knowledge_txt_chunks)} dòng thông tin từ knowledge.txt.")
    except FileNotFoundError:
        print("CẢNH BÁO: Không tìm thấy tệp 'knowledge.txt'. Bỏ qua nguồn dữ liệu này.")

    if not all_text_chunks:
        print("LỖI: Không có dữ liệu nào để xử lý. Vui lòng kiểm tra lại tệp Data.csv và knowledge.txt.")
        return

    print(f"\nTổng cộng có {len(all_text_chunks)} mẩu kiến thức để xử lý.")

    # 3. Tạo embeddings cho tất cả các đoạn văn bản
    print("Đang tạo embeddings...")
    embeddings = model.encode(all_text_chunks, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')

    # 4. Xây dựng FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # 5. Lưu index và các đoạn văn bản
    faiss.write_index(index, 'knowledge_base.index')
    with open('knowledge_base_chunks.json', 'w', encoding='utf-8') as f:
        json.dump(all_text_chunks, f, ensure_ascii=False, indent=4)

    print("\nHoàn tất!")
    print("Đã tạo thành công 2 tệp 'bộ não' mới, chứa thông tin từ cả Data.csv và knowledge.txt.")


if __name__ == '__main__':
    create_knowledge_base()
