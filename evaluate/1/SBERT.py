from sentence_transformers import SentenceTransformer, util

# git clone https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
model = SentenceTransformer(r'F:\Work\Debate\MultiAgentDabateDataAnnotation\evaluate\all-MiniLM-L6-v2')  # 多标签语义对比Multi labels sentence meaning compare

# 标签集合 A 和 B
labels_A = [
    "Code Maintainability",
    "Design Sustainability",
    "clean code",
    "confirms to well established guidelines"
]

labels_B = [
    "Clean code",
    "Sustainable design"
]

# 分别编码每个集合的标签（将每个标签看作一个句子）
emb_A = model.encode(labels_A, convert_to_tensor=True)
emb_B = model.encode(labels_B, convert_to_tensor=True)

# 对每个集合做平均池化（即：集合表示 = 各标签向量平均）
mean_emb_A = emb_A.mean(dim=0)
mean_emb_B = emb_B.mean(dim=0)

# 计算两个集合之间的语义余弦相似度
similarity = util.cos_sim(mean_emb_A, mean_emb_B).item()

print(f"余弦相似度为: {similarity:.4f}")
