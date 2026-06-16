"""
作业四：基于各组作业三数据的探索与分析
===========================================
数据来源：远端MySQL → student.csv / course.csv / sc.csv
分析内容：异常发现、可视化、组间对比、相似组发现、决策树/XGBoost分类
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")

BASE = 'D:/Three_/数据集成/第三次作业'
OUR_GROUP = 27

# ================================================================
# 1. 数据加载
# ================================================================
stu = pd.read_csv(f'{BASE}/student.csv')
cou = pd.read_csv(f'{BASE}/course.csv')
sc  = pd.read_csv(f'{BASE}/sc.csv')

print(f"student: {stu.shape} | course: {cou.shape} | sc: {sc.shape}")
print(f"组数: student={stu['group_no'].nunique()}, course={cou['group_no'].nunique()}, sc={sc['group_no'].nunique()}")

# ================================================================
# 2. 各组基础统计
# ================================================================
# 每组学生数、课程数、选课数、性别比、专业数
g_stu = stu.groupby('group_no').agg(
    stu_cnt=('student_id','count'),
    male_ratio=('gender', lambda x: (x=='男').sum()/len(x)),
    major_cnt=('department','nunique'),
).reset_index()

g_cou = cou.groupby('group_no').agg(
    cou_cnt=('course_id','count'),
    share_ratio=('share_flag', lambda x: (x=='Y').sum()/len(x)),
).reset_index()

g_sc = sc.groupby('group_no').agg(
    sc_cnt=('course_id','count'),
    sc_per_stu=('student_id', lambda x: len(x)/x.nunique()),
    avg_score=('score', lambda x: pd.to_numeric(x, errors='coerce').mean()),
).reset_index()

# 合并
g_all = g_stu.merge(g_cou, on='group_no').merge(g_sc, on='group_no')
g_all['score_std'] = sc.groupby('group_no')['score'].apply(
    lambda x: pd.to_numeric(x, errors='coerce').std()
).values

print("\n=== 各组统计描述 ===")
print(g_all.describe())

# ================================================================
# 3. 本组(27) vs 全量对比
# ================================================================
our = g_all[g_all['group_no'] == OUR_GROUP].iloc[0]
all_mean = g_all.drop(columns=['group_no']).mean()
all_std = g_all.drop(columns=['group_no']).std()

print(f"\n=== 组{OUR_GROUP} vs 全量均值 ===")
for col in ['stu_cnt','male_ratio','major_cnt','cou_cnt','share_ratio','sc_cnt','sc_per_stu','avg_score']:
    v = our[col]
    m = all_mean[col]
    s = all_std[col]
    z = (v - m) / s if s > 0 else 0
    flag = '★异常' if abs(z) > 2 else ''
    print(f"  {col}: 本组={v:.2f}  全量均值={m:.2f}±{s:.2f}  z={z:+.2f} {flag}")

# ================================================================
# 4. 异常检测
# ================================================================
print("\n=== 异常组检测（|z|>2） ===")
from scipy.stats import zscore
anomalies = {}
for col in ['stu_cnt','male_ratio','cou_cnt','share_ratio','sc_cnt','sc_per_stu','avg_score']:
    z = np.abs(zscore(g_all[col].fillna(g_all[col].mean())))
    abnormal = g_all[z > 2][['group_no', col]]
    if len(abnormal) > 0:
        for _, row in abnormal.iterrows():
            key = row['group_no']
            if key not in anomalies:
                anomalies[key] = []
            anomalies[key].append(f"{col}={row[col]:.2f}")
        print(f"  {col}: {list(abnormal['group_no'].values)}")

# 各院系学生数一致性检查
print("\n=== 各院系数据完整性检查 ===")
for col_name, df in [('student', stu), ('course', cou), ('sc', sc)]:
    dept_check = df.groupby(['group_no','dept_no']).size().unstack(fill_value=0)
    incomplete = dept_check[(dept_check[['A','B','C']] == 0).any(axis=1)]
    if len(incomplete) > 0:
        print(f"  {col_name} 缺少院系的组: {list(incomplete.index)}")
    else:
        print(f"  {col_name}: 所有组三院系数齐全")

# ================================================================
# 5. 可视化
# ================================================================
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# 5.1 各组学生数
ax = axes[0,0]
bars = g_all.set_index('group_no')['stu_cnt'].sort_values().plot(kind='barh', ax=ax)
ax.axvline(150, color='red', linestyle='--', label='标准150')
ax.axvline(our['stu_cnt'], color='green', linestyle='-', linewidth=2, label=f'组{OUR_GROUP}')
ax.set_title('各组学生总数'); ax.legend()

# 5.2 各组课程数
ax = axes[0,1]
g_all.set_index('group_no')['cou_cnt'].sort_values().plot(kind='barh', ax=ax)
ax.axvline(30, color='red', linestyle='--', label='标准30')
ax.axvline(our['cou_cnt'], color='green', linewidth=2, label=f'组{OUR_GROUP}')
ax.set_title('各组课程总数'); ax.legend()

# 5.3 各组选课数
ax = axes[0,2]
g_all.set_index('group_no')['sc_cnt'].sort_values().plot(kind='barh', ax=ax)
ax.axvline(750, color='red', linestyle='--', label='标准750')
ax.axvline(our['sc_cnt'], color='green', linewidth=2, label=f'组{OUR_GROUP}')
ax.set_title('各组选课总数'); ax.legend()

# 5.4 男生比例
ax = axes[1,0]
g_all.set_index('group_no')['male_ratio'].sort_values().plot(kind='barh', ax=ax)
ax.axvline(0.5, color='red', linestyle='--', label='均衡0.5')
ax.axvline(our['male_ratio'], color='green', linewidth=2, label=f'组{OUR_GROUP}')
ax.set_title('各组男生比例'); ax.legend()

# 5.5 平均成绩
ax = axes[1,1]
g_all.set_index('group_no')['avg_score'].sort_values().plot(kind='barh', ax=ax, color='steelblue')
ax.axvline(our['avg_score'], color='green', linewidth=2, label=f'组{OUR_GROUP}')
ax.set_title('各组平均成绩'); ax.legend()

# 5.6 成绩分布箱线图
ax = axes[1,2]
score_data = sc.copy()
score_data['score_num'] = pd.to_numeric(score_data['score'], errors='coerce')
score_pivot = [score_data[score_data['group_no']==g]['score_num'].dropna().values
               for g in sorted(g_all['group_no'].unique())]
ax.boxplot(score_pivot, labels=sorted(g_all['group_no'].unique()))
ax.axhline(our['avg_score'], color='green', linewidth=2, label=f'组{OUR_GROUP}均值')
ax.set_title('各组成绩分布'); ax.legend()
ax.tick_params(axis='x', rotation=90, labelsize=8)

plt.tight_layout()
plt.savefig(f'{BASE}/hw4_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print("\n可视化已保存: hw4_overview.png")

# ================================================================
# 6. 散点图矩阵 - 组间特征可视化
# ================================================================
features = ['stu_cnt','cou_cnt','sc_cnt','male_ratio','share_ratio','sc_per_stu','avg_score','major_cnt']
feat_data = g_all.set_index('group_no')[features].dropna()

fig, axes = plt.subplots(2, 2, figsize=(14, 12))
pairs = [('stu_cnt','sc_cnt'), ('male_ratio','avg_score'), ('share_ratio','sc_per_stu'), ('cou_cnt','avg_score')]
for (x,y), ax in zip(pairs, axes.flat):
    ax.scatter(feat_data[x], feat_data[y], alpha=0.7)
    ax.scatter(feat_data.loc[OUR_GROUP, x], feat_data.loc[OUR_GROUP, y],
               color='red', s=150, marker='*', label=f'组{OUR_GROUP}', zorder=5)
    ax.set_xlabel(x); ax.set_ylabel(y); ax.legend()
plt.tight_layout()
plt.savefig(f'{BASE}/hw4_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print("散点图已保存: hw4_scatter.png")

# ================================================================
# 7. 组间相似度分析 —— 找与本组最相似的组
# ================================================================
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean
from scipy.cluster.hierarchy import linkage, fcluster

scaler = StandardScaler()
feat_scaled = scaler.fit_transform(feat_data)
feat_df = pd.DataFrame(feat_scaled, index=feat_data.index, columns=feat_data.columns)

# 余弦相似度
cos_sim = cosine_similarity(feat_df)
cos_df = pd.DataFrame(cos_sim, index=feat_df.index, columns=feat_df.index)
our_sim = cos_df.loc[OUR_GROUP].drop(OUR_GROUP).sort_values(ascending=False)
print(f"\n=== 与组{OUR_GROUP}最相似的组（余弦相似度） ===")
for g, v in our_sim.head(5).items():
    print(f"  组{g}: {v:.4f}")

# 欧氏距离
our_vec = feat_df.loc[OUR_GROUP].values
distances = {}
for g in feat_df.index:
    if g != OUR_GROUP:
        distances[g] = euclidean(our_vec, feat_df.loc[g].values)
top_close = sorted(distances.items(), key=lambda x: x[1])[:5]
print(f"\n=== 与组{OUR_GROUP}欧氏距离最近的组 ===")
for g, d in top_close:
    print(f"  组{g}: {d:.4f}")

# 层次聚类
linkage_matrix = linkage(feat_scaled, method='ward')
clusters = fcluster(linkage_matrix, t=4, criterion='maxclust')
feat_data['cluster'] = clusters
our_cluster = feat_data.loc[OUR_GROUP, 'cluster']
same_cluster = feat_data[feat_data['cluster'] == our_cluster].index.tolist()
print(f"\n=== 层次聚类（4类）—— 组{OUR_GROUP}在第{our_cluster}类 ===")
print(f"  同类组: {[g for g in same_cluster if g != OUR_GROUP]}")

# ================================================================
# 8. 决策树分类：预测组特征类别
# ================================================================
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.model_selection import cross_val_score

# 基于成绩中位数将组分为"高分组"和"低分组"
g_all['score_label'] = (g_all['avg_score'] >= g_all['avg_score'].median()).astype(int)
dt_X = g_all[['stu_cnt','male_ratio','major_cnt','cou_cnt','share_ratio','sc_per_stu']].fillna(0)
dt_y = g_all['score_label']

dt = DecisionTreeClassifier(max_depth=3, random_state=42)
dt.fit(dt_X, dt_y)
dt_score = cross_val_score(dt, dt_X, dt_y, cv=min(5, len(dt_X))).mean()
print(f"\n=== 决策树分类 ===")
print(f"  交叉验证准确率: {dt_score:.4f}")
print(f"  特征重要性:")
for feat, imp in sorted(zip(dt_X.columns, dt.feature_importances_), key=lambda x: -x[1]):
    print(f"    {feat}: {imp:.4f}")

fig, ax = plt.subplots(figsize=(14, 8))
plot_tree(dt, feature_names=list(dt_X.columns),
          class_names=['低分组','高分组'], filled=True, rounded=True, ax=ax, fontsize=9)
plt.savefig(f'{BASE}/hw4_decision_tree.png', dpi=150, bbox_inches='tight')
plt.close()
print("  决策树图已保存: hw4_decision_tree.png")

# ================================================================
# 9. XGBoost分类
# ================================================================
try:
    from xgboost import XGBClassifier
    xgb = XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1,
                        random_state=42, verbosity=0)
    xgb.fit(dt_X, dt_y)
    xgb_score = cross_val_score(xgb, dt_X, dt_y, cv=min(5, len(dt_X))).mean()
    print(f"\n=== XGBoost分类 ===")
    print(f"  交叉验证准确率: {xgb_score:.4f}")
    print(f"  特征重要性:")
    for feat, imp in sorted(zip(dt_X.columns, xgb.feature_importances_), key=lambda x: -x[1]):
        print(f"    {feat}: {imp:.4f}")
except ImportError:
    print("\n[XGBoost] 未安装，跳过。安装: pip install xgboost")

# ================================================================
# 10. 院系级详细分析（本组）
# ================================================================
print(f"\n=== 组{OUR_GROUP}院系级分析 ===")

# 学生
our_stu = stu[stu['group_no'] == OUR_GROUP]
for dept in ['A','B','C']:
    d = our_stu[our_stu['dept_no'] == dept]
    male_r = (d['gender'] == '男').sum() / len(d) if len(d) > 0 else 0
    major_n = d['department'].nunique()
    print(f"  院系{dept}: {len(d)}学生, 男生比{male_r:.1%}, {major_n}专业")

# 课程共享
our_cou = cou[cou['group_no'] == OUR_GROUP]
for dept in ['A','B','C']:
    d = our_cou[our_cou['dept_no'] == dept]
    share_r = (d['share_flag'] == 'Y').sum() / len(d) if len(d) > 0 else 0
    print(f"  院系{dept}: {len(d)}课程, 共享率{share_r:.1%}")

# 选课
our_sc = sc[sc['group_no'] == OUR_GROUP]
for dept in ['A','B','C']:
    d = our_sc[our_sc['dept_no'] == dept]
    sc_mean = pd.to_numeric(d['score'], errors='coerce').mean()
    sc_std = pd.to_numeric(d['score'], errors='coerce').std()
    print(f"  院系{dept}: {len(d)}选课, 均分{sc_mean:.1f}±{sc_std:.1f}")

# ================================================================
# 11. 相关性热力图
# ================================================================
fig, ax = plt.subplots(figsize=(10, 8))
corr = feat_data.drop(columns=['cluster']).corr()
sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdBu_r', center=0, ax=ax)
ax.set_title('组特征相关性热力图')
plt.tight_layout()
plt.savefig(f'{BASE}/hw4_corr_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("\n相关热力图已保存: hw4_corr_heatmap.png")

print("\n" + "="*60)
print("分析完成。输出文件：")
print(f"  {BASE}/hw4_overview.png       - 各组概览(6图)")
print(f"  {BASE}/hw4_scatter.png        - 散点图矩阵")
print(f"  {BASE}/hw4_decision_tree.png  - 决策树可视化")
print(f"  {BASE}/hw4_corr_heatmap.png   - 相关性热力图")
print("="*60)
