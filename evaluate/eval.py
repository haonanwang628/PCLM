from sentence_transformers import SentenceTransformer, util
from utils.Function import import_json, save_json
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import torch
from scipy.spatial import ConvexHull, QhullError

# git clone https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
# pip install sentence-transformers
# pip install protobuf==3.20.3

model_path = r'F:\Work\Debate\MultiAgentDabateDataAnnotation\evaluate\all-MiniLM-L6-v2'
model = SentenceTransformer(model_path)


# Calculate mean cosine semantic similarity
def cosine_similarity(codes_A, codes_B):
    # Encode the labels of each set separately (treat each label as a sentence)
    emb_A = model.encode(codes_A, convert_to_tensor=True)
    emb_B = model.encode(codes_B, convert_to_tensor=True)

    # Perform average pooling on each set (i.e. set representation = average of each label vector)
    mean_emb_A = emb_A.mean(dim=0)
    mean_emb_B = emb_B.mean(dim=0)

    # Calculate the semantic cosine similarity between two sets
    similarity_mean = util.cos_sim(mean_emb_A, mean_emb_B).item()

    # Get the cosine similarity matrix: shape [len(A), len(B)]
    similarity_matrix = util.cos_sim(emb_A, emb_B)

    max_A_to_B = torch.max(similarity_matrix, dim=1).values
    max_B_to_A = torch.max(similarity_matrix, dim=0).values
    soft_jaccard = ((max_A_to_B.mean() + max_B_to_A.mean()) / 2).item()

    return similarity_mean, similarity_matrix, soft_jaccard


def cluster(codes, eps=0.3, min_samples=1):
    # dist_matrix
    embeddings = model.encode(codes, convert_to_tensor=True)
    embeddings_np = embeddings.cpu().numpy()
    similarity_matrix = util.cos_sim(embeddings, embeddings).cpu().numpy().round(3)
    dist_matrix = 1 - similarity_matrix

    # DBSCAN
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
    cluster_ids = clustering.fit_predict(dist_matrix)

    # 降维
    # reduced = PCA(n_components=2).fit_transform(embeddings_np)
    tsne = TSNE(n_components=2, perplexity=min(30, len(codes) - 1), random_state=42, metric='cosine')
    reduced = tsne.fit_transform(embeddings_np)
    # 去除噪声点
    mask = cluster_ids != -1
    filtered_embeddings = embeddings_np[mask]
    filtered_labels = cluster_ids[mask]

    if len(set(filtered_labels)) > 1:
        silhouette = silhouette_score(filtered_embeddings, filtered_labels)
        ch_score = calinski_harabasz_score(filtered_embeddings, filtered_labels)
        db_score = davies_bouldin_score(filtered_embeddings, filtered_labels)

        print(f"Silhouette Score: {silhouette:.4f}")
        print(f"Calinski-Harabasz Score: {ch_score:.4f}")
        print(f"Davies-Bouldin Score: {db_score:.4f}")
    else:
        print("无法计算指标：有效聚类簇数不足")
    return cluster_ids, reduced


def plot_clusters_polygon(cluster_ids, reduced, codes):
    df = pd.DataFrame({
        'x': reduced[:, 0],
        'y': reduced[:, 1],
    })
    df["label"] = cluster_ids
    df["text"] = ""
    # df["text"] = codes

    plt.figure(figsize=(14, 12))
    palette = sns.color_palette("tab20", len(np.unique(cluster_ids)))

    for cluster_id in np.unique(cluster_ids):
        cluster_df = df[df["label"] == cluster_id]
        points = cluster_df[["x", "y"]].values
        color = palette[cluster_id % len(palette)]

        # 点散点图
        plt.scatter(points[:, 0], points[:, 1], s=60, color=color, label=f"Cluster {cluster_id}")

        # 文本标注
        for _, row in cluster_df.iterrows():
            plt.text(row["x"] + 4, row["y"] + 4, row["text"], fontsize=8)

        # 用 ConvexHull 将簇内点围起来
        if len(points) >= 3:
            try:
                hull = ConvexHull(points)
                hull_points = points[hull.vertices]
                # 闭合多边形
                hull_points = np.concatenate([hull_points, hull_points[:1]])
                plt.plot(hull_points[:, 0], hull_points[:, 1], linestyle='-', linewidth=1.2, color=color)
                plt.fill(hull_points[:, 0], hull_points[:, 1], color=color, alpha=0.1)
            except QhullError:
                sorted_points = points[np.argsort(points[:, 0])]
                if len(np.unique(sorted_points, axis=0)) > 1:  # 排除完全共点
                    plt.plot(sorted_points[:, 0], sorted_points[:, 1], linestyle='-', linewidth=1.2, color=color,
                             alpha=0.5)
        elif len(points) == 2:
            # 直接连线
            plt.plot(points[:, 0], points[:, 1], linestyle='-', linewidth=1.5, color=color, alpha=0.7)

    plt.title(f"Cluster Visualization(num:{max(cluster_ids) + 1})")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.xlim(df['x'].min() - 50, df['x'].max() + 50)
    plt.ylim(df['y'].min() - 50, df['y'].max() + 50)
    plt.grid(True)
    # plt.legend()
    plt.axis('off')
    plt.tight_layout()
    plt.show()

    # cohen kappa


if __name__ == '__main__':
    Codebook = import_json(r"F:\Work\Debate\MultiAgentDabateDataAnnotation\Data\Scrum-interviews\output\codebook0.json")
    Codebook1 = import_json(
        r"F:\Work\Debate\MultiAgentDabateDataAnnotation\Data\Scrum-interviews\output\codebook1.json")
    all_mean_similarity = []
    all_soft_jaccard = []
    all_similarity_matrix_df = []
    code_debs, code_gts = [], []
    # 1. 一致性比较
    for codebook in Codebook:
        code_deb = [code["code"] for code in codebook["Codebook"]]
        code_gt = codebook["Code_GroundTruth"]
        code_debs += code_deb
        code_gts += code_gt
        mean_similarity, similarity_matrix_df, soft_jaccard = cosine_similarity(code_deb, code_gt)

        # cos/jaccard
        all_mean_similarity.append([round(mean_similarity, 3)])
        all_soft_jaccard.append(round(soft_jaccard, 3))
        #
        similarity_matrix_df = pd.DataFrame(
            similarity_matrix_df.cpu().numpy(),
            index=code_deb,
            columns=code_gt
        ).round(3)
        # cos_matrix
        print(similarity_matrix_df)
        all_similarity_matrix_df.append(similarity_matrix_df)
    # print(all_similarity_matrix_df)
    print(all_mean_similarity)
    print(all_soft_jaccard)

    # DBSCAN
    # 2.语义结构扰动分析
    print("--------------------------")
    print("Human labeled")
    cluster_ids, reduced = cluster(code_gts)
    plot_clusters_polygon(cluster_ids, reduced, code_gts)

    print("--------------------------")
    print("LLM labeled(positionality0)")
    cluster_ids, reduced = cluster(code_debs)
    plot_clusters_polygon(cluster_ids, reduced, code_debs)

    # 3，positionality的影响分析
    code_debs1 = []
    for codebook in Codebook1:
        code_deb1 = [code["code"] for code in codebook["Codebook"]]
        code_debs1 += code_deb1
    print("--------------------------")
    print("LLM labeled(positionality1)")
    cluster_ids, reduced = cluster(code_debs1)
    plot_clusters_polygon(cluster_ids, reduced, code_debs1)

    # 4. pre vs post
    codes_pre = []
    for codebook in Codebook:
        code_pre_roles = [code["codebook"] for code in codebook["Codebook_Pre"]]
        code_pre = [code["code"] for i in range(3) for code in code_pre_roles[i]]
        codes_pre += code_pre
    print("--------------------------")
    print("LLM labeled(positionality0 pre)")
    cluster_ids, reduced = cluster(codes_pre)
    plot_clusters_polygon(cluster_ids, reduced, codes_pre)
