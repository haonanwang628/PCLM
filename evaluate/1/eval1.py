import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import beta, norm, uniform, gaussian_kde, kstest

# ====== 在这里换成你自己的数据 ======
data = np.array([
    0.912, 0.768, 0.855, 0.868, 0.779, 0.562, 0.394,
    0.526, 0.332, 0.585, 0.895, 0.573, 0.788, 0.411,
    0.534, 0.697, 0.45, 0.595, 0.638, 0.844
])

# ====== KDE 经验分布 ======
x = np.linspace(0, 1, 200)
kde = gaussian_kde(data)
y_kde = kde(x)

# ====== Beta 拟合 ======
a, b, loc_b, scale_b = beta.fit(data, floc=0, fscale=1)
y_beta = beta.pdf(x, a, b, loc=loc_b, scale=scale_b)

# ====== Normal 拟合 ======
mu, sigma = norm.fit(data)
y_norm = norm.pdf(x, mu, sigma)

# ====== Uniform 拟合 ======
loc_u, scale_u = uniform.fit(data)
y_uni = uniform.pdf(x, loc_u, scale_u)

# ====== K-S 检验 ======
D_beta, p_beta = kstest(data, 'beta', args=(a, b, loc_b, scale_b))
D_norm, p_norm = kstest(data, 'norm', args=(mu, sigma))
D_uni, p_uni = kstest(data, 'uniform', args=(loc_u, scale_u))

print("K-S Test Results:")
print(f"  Beta   : D={D_beta:.3f}, p={p_beta:.3f}")
print(f"  Normal : D={D_norm:.3f}, p={p_norm:.3f}")
print(f"  Uniform: D={D_uni:.3f}, p={p_uni:.3f}")

# ====== 绘图 ======
plt.figure(figsize=(10,6))
plt.hist(data, bins=8, density=True, alpha=0.4, color="gray", edgecolor="black", label="Histogram")
plt.plot(x, y_kde, "r--", lw=2, label="KDE (Empirical)")
plt.plot(x, y_beta, "b-", lw=2, label=f"Beta (a={a:.2f}, b={b:.2f}), p={p_beta:.3f}")
plt.plot(x, y_norm, "g-", lw=2, label=f"Normal (μ={mu:.2f}, σ={sigma:.2f}), p={p_norm:.3f}")
plt.plot(x, y_uni, "m-", lw=2, label=f"Uniform [{loc_u:.2f}, {scale_u:.2f}], p={p_uni:.3f}")

plt.xlabel("Value")
plt.ylabel("Density")
plt.title("Distribution Fitting: Beta vs Normal vs Uniform vs KDE")
plt.legend()
plt.grid(alpha=0.3)
plt.show()

q = 0.8
beta_threshold = beta.ppf(q, a, b)
normal_threshold = norm.ppf(q, mu, sigma)

print("Beta分布阈值 (5%分位点):", beta_threshold)
print("正态分布阈值 (5%分位点):", normal_threshold)