# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Mã Khoa Học
**Nhóm:** 13
**Ngày:** 10/4/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> High cosine similarity có nghĩa là hai vector (câu, văn bản, embedding) có hướng gần như trùng nhau, tức là chúng biểu diễn nội dung có ý nghĩa tương tự nhau trong không gian embedding, bất kể độ dài hay magnitude khác nhau.

**Ví dụ HIGH similarity:**
- Sentence A: "The cat sits on the mat."
- Sentence B: "A cat is sitting on the rug."
- Tại sao tương đồng: Cả hai câu đều mô tả cùng một hành động (mèo ngồi) trên một bề mặt (thảm/chiếu), chủ ngữ và cấu trúc ngữ nghĩa gần như giống hệt.

**Ví dụ LOW similarity:**
- Sentence A: "The cat sits on the mat."
- Sentence B: "The rocket launches into space."
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác nhau (động vật trong nhà vs. hàng không vũ trụ), không có từ khóa hoặc ngữ nghĩa chung.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> 
Cosine similarity chỉ quan tâm đến góc (hướng) giữa hai vector, không bị ảnh hưởng bởi độ dài văn bản (magnitude), trong khi Euclidean distance bị chi phối bởi độ dài – hai câu dài khác chủ đề nhưng có thể gần nhau về khoảng cách Euclid, ngược lại hai câu ngắn cùng nghĩa nhưng dài khác nhau lại có thể xa nhau.



### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> *Đáp án:*

Mỗi chunk có 500 ký tự, nhưng chunk sau lấy 50 ký tự từ chunk trước → số ký tự mới thực tế mỗi chunk = 500 - 50 = 450 ký tự (trừ chunk đầu tiên).
Chunk 1: ký tự 1 → 500
Chunk 2: ký tự 451 → 950
Chunk 3: ký tự 901 → 1400

Tổng quát: chunk thứ i bắt đầu ở vị trí 1 + (i-1) × (500 - 50) = 1 + (i-1) × 450.
Cần tìm n sao cho: 1 + (n-1) × 450 ≤ 10000 - 500 + 1?
Cách nhanh: number_of_chunks = ⌈(total_chars - chunk_size) / (chunk_size - overlap)⌉ + 1
= ⌈(10000 - 500) / (500 - 50)⌉ + 1 = ⌈9500 / 450⌉ + 1 = ⌈21.111...⌉ + 1 = 22 + 1 = 23

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**

> Overlap tăng lên 100 làm số chunks tăng lên (vì bước nhảy mỗi chunk giảm còn 500-100=400), với 10,000 ký tự sẽ là ⌈(10000-500)/400⌉+1 = ⌈9500/400⌉+1 = 24+1 = 25 chunks. Overlap nhiều hơn giúp giữ ngữ cảnh liên tục tốt hơn ở biên giữa các chunks, tránh mất thông tin khi một ý hoặc câu bị cắt đôi.
---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Luật, các kiến thức về luật

**Tại sao nhóm chọn domain này?**
> Luật dễ tìm tài liệu và ít có tài liệu bị sai, thông tin sai lệch.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | 01_luat_giao_thong_duong_bo.txt | Thư viện pháp luật | 22,218 | {"source": "data\01_luat_giao_thong_duong_bo.txt", "category": "Luật Giao thông", "date": "2008-11-13", "urgency_level": "High"} |
| 2 | luat_hon_nhan.txt | Thư viện pháp luật | 87,372 |   {"source": "data/luat_hon_nhan.txt", "category": "Luật Dân sự", "date": "2014-06-19", "urgency_level": "Medium"} |
| 3 | luat_nvqs.txt | Thư viện pháp luật | 46,824 |   {"source": "data/luat_nvqs.txt", "category": "Luật Hành chính", "date": "2015-06-19", "urgency_level": "High"} |
| 4 | luat_tieu_dung.txt | Thư viện pháp luật | 220,785 |   {"source": "data/luat_tieu_dung.txt", "category": "Luật Kinh tế", "date": "2020-08-26", "urgency_level": "Medium"} |
| 5 | luathinhsu.txt | Thư viện pháp luật | 31,866 |   {"source": "data/luathinhsu.txt", "category": "Luật Hình sự", "date": "2015-11-27", "urgency_level": "Critical"} |
| 6 | LuatLaoDong.txt | Thư viện pháp luật | 190,659 |   {"source": "data/LuatLaoDong.txt", "category": "Luật Lao động", "date": "2019-11-20", "urgency_level": "High"} |

### Metadata Schema

Dưới đây là bảng metadata đã được điền đầy đủ, dựa trên yêu cầu của bạn và đoạn code cung cấp:

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| source | string | `"policy_2025.pdf"` | Giúp truy vết lại tài liệu gốc khi cần kiểm tra đầy đủ nội dung. |
| category | string | `"FAQ"`, `"SOP"`, `"policy"` | Lọc nhanh theo loại tài liệu, tránh nhiễu giữa các domain khác nhau. |
| date | string (ISO) | `"2025-03-01"` | Hỗ trợ ưu tiên tài liệu mới hơn hoặc lọc theo khoảng thời gian. |
| language | string | `"vi"`, `"en"` | Chọn đúng ngôn ngữ cho câu hỏi, đặc biệt khi hệ thống đa ngữ. |
| extension | string | `".pdf"`, `".docx"`, `".md"` | Dùng để xử lý đặc thù theo định dạng (ví dụ: parse lại nếu cần). |
| chunk_index | int | `0`, `1`, `2` | Giữ đúng thứ tự các đoạn khi ghép lại hoặc hiển thị kết quả. |
| chunker | string | `"fixed_size"` | Ghi nhớ phương pháp chia đoạn, hữu ích khi thử nghiệm hoặc debug. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu                     | Strategy                           | Chunk Count | Avg Length | Preserves Context?        |
|-----------------------------|------------------------------------|-------------|------------|---------------------------|
| luat_nghia_vu_quan_su.txt   | FixedSizeChunker (fixed_size)    | 235         | 199.25     | Trung bình                |
| luat_nghia_vu_quan_su.txt   | SentenceChunker (by_sentences)   | 136         | 341.90     | Tốt                       |
| luat_nghia_vu_quan_su.txt   | RecursiveChunker (recursive)     | 356         | 129.69     | Kém (bị vỡ nhỏ)           |
| luat_hinh_su.txt            | FixedSizeChunker (fixed_size)    | 160         | 199.16     | Trung bình                |
| luat_hinh_su.txt            | SentenceChunker (by_sentences)   | 82          | 386.18     | Tốt                       |
| luat_hinh_su.txt            | RecursiveChunker (recursive)     | 256         | 122.71     | Kém (bị vỡ nhỏ)           |
| luat_tieu_dung.txt          | FixedSizeChunker (fixed_size)    | 1104        | 199.99     | Trung bình                |
| luat_tieu_dung.txt          | SentenceChunker (by_sentences)   | 341         | 645.11     | Rất tốt (nhưng hơi dài)   |
| luat_tieu_dung.txt          | RecursiveChunker (recursive)     | 1664        | 130.86     | Kém (quá nhiều chunk nhỏ) |

### Strategy Của Tôi

**Loại:** FixedSizeChunker 
**Mô tả cách hoạt động:**
> FixedSizeChunker chia văn bản thành các đoạn có độ dài ký tự cố định, ví dụ chunk_size=500, và cho phép các đoạn liền kề chồng lấp một phần qua overlap=50. Mỗi chunk được tạo theo cơ chế sliding window nên nội dung dài sẽ không bị mất khi đi qua ranh giới chunk. Dấu hiệu để tách chunk ở strategy này không dựa vào ngữ nghĩa hay câu, mà dựa vào vị trí ký tự. Cách này giúp tạo kích thước chunk ổn định, dễ kiểm soát số lượng chunk và chi phí embedding.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Domain luật có văn bản dài, nhiều điều khoản và cách diễn đạt lặp lại, nên fixed-size giúp bao phủ dữ liệu đều và tránh bỏ sót vùng thông tin khi truy hồi. Overlap hỗ trợ giữ ngữ cảnh ở các đoạn cắt giữa điều khoản, giảm nguy cơ mất ý quan trọng nằm ở ranh giới chunk. Ngoài ra strategy này đơn giản, ổn định, dễ benchmark với các cấu hình khác trong nhóm.

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| luat_nghia_vu_quan_su.txt   | Của tôi  | 136         | 341.90     | Tốt                       |
| luat_hinh_su.txt            | best    | 160         | 199.16     | Trung bình                |

### So Sánh Với Thành Viên Khác
| Thành viên       | Strategy         | Retrieval Score (/10) | Điểm mạnh                                                                                                                                                                                                | Điểm yếu                                                                                                                             |
| ---------------- | ---------------- | --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Tôi              | FixedSizeChunker | 9/10                  | Dễ triển khai và kiểm soát tốt kích thước chunk, giúp đảm bảo tính đồng nhất về số token và hạn chế lỗi vượt quá giới hạn context của mô hình.                                                           | Có nguy cơ cắt ngang các điều luật, làm gián đoạn nội dung và dẫn đến việc mô hình RAG hiểu sai hoặc thiếu chính xác.                |
| Nguyễn Tuấn Kệt  | SentenceChunker  | 10/10                 | Bảo toàn trọn vẹn ý nghĩa của từng câu, tránh hiện tượng đứt đoạn và đảm bảo tính tự nhiên của văn bản—đặc biệt quan trọng đối với tài liệu pháp lý. Ngữ cảnh truy xuất rõ ràng và có tính liên kết cao. | Độ dài các chunk không đồng đều, có thể quá ngắn hoặc quá dài, gây khó khăn trong việc tối ưu giới hạn batch và quá trình embedding. |
| Trần Ngô Hồng Hà | FixedSizeChunker | 9/10                  | Linh hoạt trong việc điều chỉnh các tham số như `chunk_size` và `overlap`. Tốc độ xử lý nhanh, phù hợp với khối lượng văn bản lớn.                                                                       | Tương tự phương pháp trên, nếu cấu hình `overlap` không hợp lý sẽ dễ làm mất tính liên tục của ngữ cảnh pháp lý.                     |


**Strategy nào tốt nhất cho domain này? Tại sao?**
> Sentence tốt nhất vì giữ được context tốt hơn.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Mình dùng regex (?<=[.!?])(?:\s+|\n) để tách câu theo dấu kết thúc câu (., !, ?) và khoảng trắng/xuống dòng phía sau. Sau khi split, mình strip() từng câu và loại bỏ phần rỗng để tránh tạo chunk rác. Edge case được xử lý gồm text rỗng, text chỉ có khoảng trắng, và trường hợp max_sentences_per_chunk <= 0 thì ép về tối thiểu 1 câu/chunk.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Thuật toán thử tách theo danh sách separator ưu tiên (\n\n -> \n -> . -> -> ""), nếu đoạn vẫn quá dài thì đệ quy với separator kế tiếp. Base case là: đoạn hiện tại rỗng thì trả [], hoặc độ dài <= chunk_size thì trả luôn [current_text]. Nếu hết separator (hoặc separator rỗng), mình fallback cắt cứng theo chunk_size để đảm bảo luôn sinh được chunk hợp lệ.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> add_documents embed từng Document.content, đóng gói thành record gồm id, content, embedding, metadata (kèm doc_id) rồi lưu vào Chroma hoặc in-memory list. search embed query rồi tính điểm tương đồng với từng record; ở in-memory dùng dot product để rank giảm dần, ở Chroma lấy distance và đổi sang score = 1 - distance. Cuối cùng trả top-k kết quả gồm content, score, metadata.

**`search_with_filter` + `delete_document`** — approach:
> search_with_filter luôn filter trước rồi mới search để đảm bảo không lẫn kết quả ngoài điều kiện metadata. Với in-memory, mình lọc list records bằng all(...); với Chroma, build where (1 điều kiện hoặc $and nhiều điều kiện) rồi query. delete_document xóa toàn bộ records theo doc_id: ở Chroma lấy ids theo where rồi delete, ở in-memory thì rebuild list bỏ các phần tử có metadata.doc_id tương ứng.

### KnowledgeBaseAgent

**`answer`** — approach:
> answer chạy retrieval trước: store.search(question, top_k) để lấy các chunk liên quan nhất. Sau đó inject context bằng cách nối nội dung các chunk thành block Context: rồi ghép với Question: thành prompt cuối cùng. Prompt structure đơn giản theo RAG pattern: Context + Question, rồi đưa cho llm_fn để sinh câu trả lời bám theo thông tin đã retrieve.

### Test Results

```
plugins: anyio-4.13.0
collected 42 items                                                                                                            

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                   [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                            [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                     [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                      [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                           [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                           [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                 [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                  [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                  [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                  [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                             [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                         [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                   [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                          [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                              [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                        [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                              [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                  [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                    [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                      [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                            [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                 [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                   [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                       [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                    [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                             [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                            [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                       [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                   [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                              [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                  [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                        [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                  [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED               [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                             [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                            [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                           [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                    [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED          [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED              [100%]

===================================================== 42 passed in 0.26s =====================================================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Công dân nam đủ 18 tuổi phải đăng ký nghĩa vụ quân sự. | Nam công dân đến tuổi luật định phải thực hiện đăng ký NVQS. | high | 0.91 | Đúng |
| 2 | Người tiêu dùng có quyền khiếu nại và yêu cầu bồi thường. | Khách hàng được quyền phản ánh và đòi bồi hoàn khi quyền lợi bị xâm phạm. | high | 0.88 | Đúng |
| 3 | Vợ chồng có nghĩa vụ tôn trọng và hỗ trợ lẫn nhau. | Đua xe trái phép là hành vi bị nghiêm cấm. | low | 0.22 | Đúng |
| 4 | Các hành vi bị cấm trong giao thông đường bộ phải bị xử lý nghiêm. | Những vi phạm giao thông nghiêm trọng sẽ bị chế tài theo pháp luật. | high | 0.79 | Đúng |
| 5 | Hình phạt tù có thời hạn là một loại hình phạt chính. | Người lao động được trả lương đúng thời hạn theo hợp đồng. | low | 0.31 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Bất ngờ nhất là cặp 5 vẫn có điểm trên 0.3 dù khác chủ đề (hình sự và lao động). Điều này cho thấy embedding vẫn có thể tạo tương đồng bề mặt khi hai câu cùng văn phong pháp lý và có một số từ/cấu trúc gần nhau. Vì vậy khi đánh giá retrieval cần kết hợp metadata/filter và không nên chỉ dựa vào score tuyệt đối.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| #  | Loại query | Query | Gold Answer |
| -- | ---------- | ----- | ----------- |
| 1 | Phức tạp, đa tài liệu | "Nếu một cá nhân có hành vi trốn tránh nghĩa vụ quân sự, đồng thời thực hiện hành vi kinh doanh hàng hóa không rõ nguồn gốc hoặc thay đổi nhãn mác (đè tem) thì sẽ bị xem xét xử lý như thế nào theo quy định của pháp luật hiện hành?" | Hai hành vi bị xử lý độc lập: (1) Trốn tránh NVQS bị xử phạt hành chính hoặc hình sự theo Luật NVQS 2015 (sửa đổi 2019); (2) Kinh doanh hàng không rõ nguồn gốc / đè tem bị xử lý theo Luật Bảo vệ người tiêu dùng và Bộ luật Hình sự về tội sản xuất/buôn bán hàng giả. Không có tình tiết giảm nhẹ chéo giữa hai hành vi. |
| 2 | Mơ hồ | "Thời hạn đi tù là bao lâu?" | Không có câu trả lời duy nhất — thời hạn tù phụ thuộc vào từng tội danh cụ thể, mức độ thiệt hại, tình tiết tăng nặng/giảm nhẹ. Retrieval nên trả về nhiều điều khoản từ nhiều luật khác nhau. Đây là query cố tình mơ hồ để kiểm tra khả năng disambiguation. |
| 3 | Không liên quan | "Công thức nấu món phở bò Nam Định truyền thống là gì?" | Không có thông tin trong corpus (corpus chỉ chứa văn bản pháp luật). Agent nên trả lời "Không tìm thấy thông tin liên quan trong tài liệu." thay vì hallucinate. |
| 4 | Trực tiếp, tra cứu điều luật | "Điều 101 Luật Giao thông đường bộ quy định về nội dung gì?" | Điều 101 Luật Giao thông đường bộ 2008 quy định về xử lý vi phạm trong lĩnh vực giao thông đường bộ — cụ thể là thẩm quyền và hình thức xử phạt vi phạm hành chính. Retrieval phải trả về đúng chunk chứa Điều 101 từ file 01_luat_giao_thong_duong_bo.txt. |
| 5 | Ngắn gọn, thực tế | "Mức phạt nồng độ cồn?" | Theo Luật Giao thông đường bộ và Nghị định xử phạt hiện hành: có 3 mức nồng độ cồn với mức phạt tương ứng từ 2–4 triệu (mức 1), 7–8 triệu (mức 2), đến 30–40 triệu + tước GPLX 22–24 tháng (mức 3) đối với ô tô. Mức phạt xe máy thấp hơn. |
### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Nếu một cá nhân có hành vi trốn tránh nghĩa vụ quân sự, đồng thời thực hiện hành vi kinh doanh hàng hóa không rõ nguồn gốc hoặc thay đổi nhãn mác (đè tem) thì sẽ bị xem xét xử lý như thế nào theo quy định của pháp luật hiện hành? | Chunk từ `luat_nvqs.txt` nêu hành vi trốn tránh NVQS bị nghiêm cấm + chunk từ `luat_tieu_dung.txt` về hành vi buôn bán/ghi nhãn sai và chế tài tương ứng. | 0.82 | Yes | Agent trả lời hai hành vi bị xử lý theo hai nhóm luật khác nhau, không gộp chung chế tài; hướng xử lý là áp dụng độc lập theo từng hành vi vi phạm. |
| 2 | Thời hạn đi tù là bao lâu? | Chunk từ `luathinhsu.txt` mô tả khung hình phạt tù có thời hạn và nguyên tắc phụ thuộc tội danh, mức độ, tình tiết vụ án. | 0.67 | Partially | Agent trả lời không có một con số cố định, thời hạn tù phụ thuộc từng tội và khung luật cụ thể; câu trả lời đúng hướng nhưng còn tổng quát. |
| 3 | Công thức nấu món phở bò Nam Định truyền thống là gì? | Top-1 trả về chunk pháp luật không liên quan (nội dung về nghĩa vụ/quy định xử phạt), không chứa thông tin ẩm thực. | 0.19 | No | Agent không tìm thấy thông tin phù hợp trong corpus pháp luật và từ chối trả lời theo hướng “không đủ dữ liệu”, tránh bịa nội dung. |
| 4 | Điều 101 Luật Giao thông đường bộ quy định về nội dung gì? | Chunk chứa Điều 101 trong `01_luat_giao_thong_duong_bo.txt`, nói về xử lý vi phạm trong lĩnh vực giao thông đường bộ. | 0.89 | Yes | Agent tóm tắt đúng nội dung chính của Điều 101: thẩm quyền/hình thức xử lý vi phạm hành chính trong giao thông đường bộ. |
| 5 | Mức phạt nồng độ cồn? | Chunk từ luật giao thông và phần xử phạt liên quan vi phạm nồng độ cồn, nêu phân mức xử phạt theo ngưỡng vi phạm. | 0.77 | Yes | Agent trả lời theo các mức vi phạm nồng độ cồn và nêu mức phạt tăng dần; có nhắc khác biệt mức xử phạt giữa ô tô và xe máy. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 4 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Mình học được cách một bạn dùng SentenceChunker để giữ trọn ý theo câu, nhờ đó các query dạng giải thích dài có kết quả mạch lạc hơn so với fixed-size trong một số trường hợp. Bạn ấy cũng chỉ ra rằng chỉ cần đổi tham số chunk hợp lý thì chất lượng retrieval cải thiện rõ rệt mà không cần đổi model embedding. Điều này giúp mình nhìn rõ vai trò của chunk coherence trong RAG.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Nhóm khác dùng metadata filter rất chủ động (theo category và language) trước khi search nên giảm nhiều kết quả nhiễu ở top-k. Mình thấy cách họ thiết kế benchmark query có chủ đích (có query bắt buộc filter) giúp đánh giá hệ thống thực tế hơn, không chỉ kiểm tra có chạy được hay không. Đây là điểm mình muốn áp dụng cho các bài sau.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Mình sẽ chuẩn hóa metadata ngay từ đầu theo schema cố định và thêm trường section để truy hồi chính xác theo điều/chương. Ngoài ra mình sẽ làm một bước làm sạch văn bản kỹ hơn (xử lý ký tự lỗi, heading không chuẩn) trước khi chunk để giảm chunk nhiễu. Cuối cùng, mình sẽ thử A/B rõ ràng hơn giữa fixed-size và sentence-based trên cùng bộ query để chọn strategy theo dữ liệu thay vì theo cảm giác.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5/ 5 |
| Document selection | Nhóm | 10/ 10 |
| Chunking strategy | Nhóm | 10/ 15 |
| My approach | Cá nhân | 10/ 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | / 10 |
| Core implementation (tests) | Cá nhân |30 / 30 |
| Demo | Nhóm | / 5 |
| **Tổng** | | 95/ 100** |
