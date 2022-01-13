# -*- coding: utf-8 -*-
"""MLT-Recommendation System.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1yi2RPA6k5RhdP4tLtoZDpN92iTj1A4lj

# Proyek Machine Learning : Recommendation System

* Topik  : Rekomendasi Produk
* Tujuan : Memberikan rekomendasi restoran berdasarkan preferensi konsumen dengan memanfaatkan popularitas dan sistem rekomendasi kolaboratif

* Dataset yang digunakan : https://www.kaggle.com/uciml/restaurant-data-with-consumer-ratings?select=rating_final.csv

## Melakukan Import terhadap Library yang diperlukan
"""

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import pandas as pd
import seaborn as sns
import scipy.sparse

import matplotlib.pyplot as plt
# %matplotlib inline

import warnings
warnings.simplefilter('ignore')

from scipy.sparse.linalg import svds
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = 'all' 
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from pandas import read_csv

"""## DATA UNDERSTANDING

### Memuat Dataset ***rating_final.csv*** pada variabel **"df"**
"""

df = read_csv('drive/MyDrive/csv/rating_final.csv')

df.head()

"""### Menampilkan distribusi rating pada dataset "df""""

df.describe()

"""### Menampilkan tipe data setiap kolom pada dataset "df""""

df.info()

"""### Menampilkan Informasi terkait dataset"""

df.describe(include = 'all').transpose()

"""### Exploratory Data Analysis (EDA)
<ul type="none">
  <li>Tahap eksplorasi penting untuk memahami variabel-variabel pada data serta korelasi antar variabel. Pemahaman terhadap variabel pada data dan korelasinya akan membantu kita dalam menentukan pendekatan atau algoritma yang cocok untuk data kita. Idealnya, kita melakukan eksplorasi data terhadap seluruh variabel.</li>
<hr>
  <li>Exploratory Data Analysis (EDA) memiliki peranan penting untuk dapat memahami dataset secara baik dan detail.
  </li>
</ul>



**Beberapa pertanyaan yang akan kita jawab dengan menggunakan EDA:**
* Jumlah pengguna unik, restoran unik, no. rating, food_ratings, service_ratings
* Berapa kali pengguna menilai
* Berapa kali restoran dinilai
* Bagaimana distribusi peringkat untuk makanan, layanan?

Kita akan mengeksplorasi data sesuai dengan pertanyaan diatas.

### Jumlah user unik, restaurant unik, rating, rating makanan, dan rating layanan yang diberikan
"""

print('unique users: ', df['userID'].nunique())
print('unique restaurant: ', df['placeID'].nunique())
print('Total number of ratings given: ', df['rating'].count())
print('Total number of food ratings given: ', df['food_rating'].count())
print('Total number of service ratings provided: ', df['service_rating'].count())

"""### Menampilkan informasi terkait berapa kali user/pengguna melakukan penilaian """

most_rated_users = df['userID'].value_counts()
most_rated_users

"""### Menampilkan informasi terkait berapa kali restoran memperoleh penilaian"""

most_rated_restaurants = df['placeID'].value_counts()
most_rated_restaurants

"""### Menampilkan visualisasi data distribusi rating"""

plt.figure(figsize = (8,5))
sns.countplot(df['rating'])

"""### Menampilkan visualisasi data distribusi rating makanan"""

plt.figure(figsize = (8,5))
sns.countplot(df['food_rating'])

"""### Menampilkan visualisasi data distribusi rating layanan"""

plt.figure(figsize = (8,5))
sns.countplot(df['service_rating'])

"""Setelah melakukan **Exploratory Data Analysis (EDA)**, kita memperoleh hasil:

- Semua (130) restoran dinilai minimal 3 kali dalam skala 0 hingga 2
- Semua (138) pengguna telah memberi peringkat minimal 3 kali

Untuk merekomendasikan restoran dengan preferensi teratas, kita dapat meminta setiap pengguna memberi peringkat terhadap semua restoran. Namun tentunya hal tersebut sedikit sulit dicapai. Solusinya kita akan mencoba memprediksi peringkat yang akan diberikan pengguna terhadap restoran.

### Membuat sekumpulan data yang memuat informasi pengguna yang aktif memberi peringkat setidaknya n kali
"""

n = 3
user_counts = most_rated_users[most_rated_users > n]
len(user_counts)
user_counts

"""#### Banyak rating yang diberikan"""

user_counts.sum()

"""#### Semua data rating yang diberikan pengguna"""

data_final = df[df['userID'].isin(user_counts.index)]
data_final

"""## DATA PREPARATION

### Mengubah data menjadi matriks
"""

final_ratings_matrix = data_final.pivot(index = 'userID', columns = 'placeID', values='rating').fillna(0)
final_ratings_matrix.head()

"""### Melakukan kalkulasi Densitas matriks


<ul type="none" align="justify">
  <li>
  Hal tersebut merupakan suatu cara untuk mengetahui banyak kemungkinan peringkat yang diberikan dan berapa tepatnya peringkat yang diberikan.
  </li>
</ul>

#### Banyak rating yang diberikan
"""

given_num_of_ratings = np.count_nonzero(final_ratings_matrix)
print('Given num of ratings: ', given_num_of_ratings )

"""#### Total banyaknya rating yang bisa diberikan"""

possible_num_of_ratings = final_ratings_matrix.shape[0] * final_ratings_matrix.shape[1]
print('Possible num of ratings: ', possible_num_of_ratings)

"""#### Menghitung Densitas matriks"""

density = (given_num_of_ratings / possible_num_of_ratings) * 100
print('density: {:4.2f}%'.format(density))

"""### Memeriksa nilai yang hilang (**missing values**) pada variabel data_final"""

data_final.isnull().sum()

"""* **NOTE** : Kita dapat melihat bahwa variabel data_final tidak memiliki nilai yang hilang (**missing value**). Dapat disimpulkan bahwa data telah bersih dan telah siap untuk dimasukkan ke dalam pemodelan.

## Modeling and Result

Pada bagian ***Modeling***, kita akan menggunakan algoritma:
- Popularity based Recommender Model
- Collaborative Filtering Model

### Popularity Based Recommender Model
Rekomendasi ini didasari apa yang sedang populer/trend. Ini akan berguna ketika kita tidak memiliki data historis sebagai referensi didalam merekomendasikan suatu produk terhadap pengguna.

**Hal yang dapat dilakukan:**
* Memperoleh jumlah pengguna yang telah memberi peringkat dari nilai rating restoran tertinggi
* Memberi peringkat berdasarkan skor
* Merekomendasikan tempat populer/trend

#### Jumlah user rating
"""

data_grouped = df.groupby('placeID').agg({'userID':'count'}).reset_index()
data_grouped.rename(columns = {'userID': 'score'}, inplace = True )
data_sort = data_grouped.sort_values(['score','placeID'], ascending = False)
data_sort.head()

"""#### Peringkat berdasarkan nilai scores"""

data_sort['Rank'] = data_sort['score'].rank(ascending = 0, method = 'first')
pop_recom = data_sort
pop_recom.head()

print('List of most popular restaurants')
pop_recom[['placeID','score','Rank']].head()

"""##### **NOTE :** karena rekomendasi ini berdasarkan popularitas dan tidak dipersonalisasi, sehingga rekomendasi tetap sama untuk semua pengguna.

### Collaborative Filtering Model

Menggunakan model based collaborative filtering : SVD(Singular Value Decomposition)

**Beberapa hal yang harus dilakukan:**
* Mengubah data menjadi tabel pivot -> Format diperlukan untuk model colab
* Membuat kolom user_index untuk menghitung no.pengguna -> mengubah konvensi penamaan pengguna dengan menggunakan penghitung
* Menerapkan metode SVD pada matriks sparse besar -> untuk memprediksi peringkat untuk semua restoran yang tidak diberi peringkat oleh pengguna
* Memprediksi peringkat untuk semua restoran yang tidak dinilai oleh pengguna menggunakan SVD
* Membungkus semuanya menjadi sebuah fungsi

#### Mengubah data menjadi pivot table
"""

pivot_data = data_final.pivot(index = 'userID', columns = 'placeID', values = 'rating').fillna(0)
pivot_data.shape
pivot_data.head()

"""#### Membuat kolom user_index untuk menghitung no.pengguna"""

pivot_data['user_index'] = np.arange(0, pivot_data.shape[0],1)
pivot_data.head()

pivot_data.set_index(['user_index'], inplace = True)
pivot_data.head()

"""#### Menerapkan metode SVD pada matriks sparse besar"""

# SVD
U,s, VT = svds(pivot_data, k = 10)

# Kontruksi diagonal array di SVD
sigma = np.diag(s)

"""##### Menerapkan SVD akan menamai 3 parameter output"""

# Matriks Ortogonal
print("U = ",U)

#Nilai tunggal
print("S = ",s)

#Transpose matriks ortogonal
print("VT = ", VT)

"""##### **NOTE :** Dapat kita lihat bahwa untuk matriks sparse, dapat menggunakan fungsi sparse.linalg.svds() untuk melakukan dekomposisi. SVD berguna untuk: kompresi data, pengurangan kebisingan mirip dengan Analisis Komponen Utama dan pengindeksan Semantik Laten (LSI), digunakan dalam pengambilan dokumen dan kesamaan kata dalam penambangan teks."""

# Prediksi peringkat untuk semua restoran yang tidak dinilai oleh pengguna menggunakan SVD
all_user_predicted_ratings = np.dot(np.dot(U,sigma), VT)

# Prediksi rating
pred_data = pd.DataFrame(all_user_predicted_ratings, columns = pivot_data.columns)
pred_data.head()

"""#### **Membungkus semua menjadi sebuah fungsi**

Beberapa hal yang harus kita dilakukan:

- Membuat fungsi untuk merekomendasikan tempat dengan peringkat prediksi tertinggi
- Menggunakan fungsi untuk merekomendasikan tempat berdasarkan ID pengguna, peringkat sebelumnya, peringkat yang diprediksi, jumlah tempat

##### Merekomendasikan tempat dengan rating prediksi tertinggi
"""

def recommend_places(userID, pivot_data, pred_data, num_recommendations):
  
  # Index mulai dari 0
  user_index = userID-1 

  # Mengsorting rating pengguna
  sorted_user_ratings = pivot_data.iloc[user_index].sort_values(ascending = False) 

  # Prediksi pengguna yang tersortir
  sorted_user_predictions = pred_data.iloc[user_index].sort_values(ascending = False) 

  temp = pd.concat([sorted_user_ratings, sorted_user_predictions], axis=1)
  temp.index.name = 'Recommended Place ID'
  temp.columns = ['user_ratings', 'user_predictions']
  temp = temp.loc[temp.user_ratings == 0]
  temp = temp.sort_values('user_predictions', ascending = False)

  print('\n Recommended place ID for Customers --> (user_id = {}):\n'.format(userID))
  print(temp.head(num_recommendations))

# Rekomendasi tempat berdasarkan pada userID, past ratings, predicted ratings, num of places
userID = 50
num_recommendations = 10
recommend_places(userID, pivot_data, pred_data, num_recommendations)

"""## EVALUATION

### Metrik Evaluasi Accuracy
"""

X = data_sort.drop(['score'], axis=1)
y = data_sort['score']
X_train, X_test, y_train, y_test = train_test_split (X, y, test_size = 0.2, random_state=256)

print(f'Total of sample in whole dataset: {len(X)}')
print(f'Total of sample in train dataset: {len(X_train)}')
print(f'Total of sample in test dataset: {len(X_test)}')

# Melatih binary classifier menggunakan Algoritma Random Forest dengan Hyperparameter default
classifier = RandomForestClassifier(random_state=19)
classifier.fit(X_train, y_train)

# X_test, y_test sebagai test data points
predictions = classifier.predict(X_test)

# Menghitung akurasi pengklasifikasi
print("\nAccuracy of the classifier is: ", accuracy_score(y_test, predictions))

"""### Metrik Evaluasi Precision"""

# Menghitung skor presisi pengklasifikasi
print("Precision Score of the classifier is: ", precision_score(y_test, predictions, pos_label='positive', average='micro' ))

"""### Evaluasi model menggunakan RMSE

RMSE adalah akar kuadrat dari rata-rata kuadrat error. Pengaruh setiap kesalahan pada RMSE sebanding dengan ukuran kesalahan kuadrat, sehingga kesalahan yang lebih besar memiliki efek besar yang tidak proporsional pada RMSE. Akibatnya, RMSE sensitif terhadap outlier.


**Beberapa hal yang harus kita dilakukan:**
* Peringkat aktual yang diberikan oleh pengguna
* Peringkat yang diprediksi untuk suatu tempat
* Hitung RMSE

#### Peringkat aktual yang diberikan oleh pengguna
"""

final_ratings_matrix.head()

"""#### Rata-rata peringkat aktual untuk setiap tempat"""

final_ratings_matrix.mean().head()

"""#### Prediksi peringkat suatu tempat"""

pred_data.head()

"""#### Rata-rata prediksi rating untuk setiap tempat"""

pred_data.mean().head()

"""#### Kalkulasi nilai RMSE"""

rmse_data = pd.concat([final_ratings_matrix.mean(), pred_data.mean()], axis = 1)
rmse_data.columns = ['Avg_actual_rating', 'Avg_predicted_ratings']

print(rmse_data.shape)
rmse_data['place_index'] = np.arange(0, rmse_data.shape[0],1)
rmse_data.head()

plt.plot(rmse_data['Avg_actual_rating'])
plt.title('rmse_data')
plt.ylabel('root_mean_squared_error')

plt.show()

plt.plot(rmse_data['Avg_predicted_ratings'])
plt.title('rmse_data')
plt.ylabel('root_mean_squared_error')

plt.show()

"""#### Nilai RMSE pada SVD Model"""

RMSE = round((((rmse_data.Avg_actual_rating - rmse_data.Avg_predicted_ratings) ** 2).mean() ** 0.5),5)
print('\n RMSE SVD Model = {}\n'.format(RMSE))

"""## CONCLUSION

Model rekomendasi berdasarkan `Popularity Based Recommender Model` tidak dipersonalisasi dan  didasarkan pada jumlah frekuensi, yang mungkin tidak sesuai untuk pengguna. Model merekomendasikan 5 tempat yang sama untuk semua pengguna tetapi model berbasis Collaborative Filtering dapat merekomendasikan seluruh daftar yang berbeda berdasarkan rating yang pengguna berikan.

Model rekomendasi berdasarkan `Collaborative Filtering`  adalah sistem rekomendasi yang dipersonalisasi, rekomendasi didasarkan pada perilaku/interaksi pengguna di masa lalu (historis) dan tidak bergantung pada informasi tambahan apa pun.
"""