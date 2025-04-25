import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
from io import BytesIO
import base64 

# Set page config
st.set_page_config(
    page_title="Analisis Hasil Ujian",
    page_icon="📊",
    layout="wide"
)

# Custom CSS untuk tampilan
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #0D47A1;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .section {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .insight-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .highlight {
        color: #D32F2F;
        font-weight: bold;
    }
    .success {
        color: #388E3C;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Fungsi untuk download dataframe sebagai CSV
def download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

# Fungsi untuk preprocessing data
def preprocess_data(df_answers, df_key=None, has_key_column=False):
    # Jika key ada dalam dataframe jawaban siswa (kolom pertama)
    if has_key_column and df_key is None:
        key_row = df_answers.iloc[0].copy()
        df_answers = df_answers.iloc[1:].copy()
        # Konversi key_row menjadi DataFrame untuk format yang konsisten
        df_key = pd.DataFrame([key_row.values], columns=key_row.index)
    
    # Bersihkan nama kolom jika diperlukan
    if df_key is not None:
        # Pastikan kolom pertama adalah nama siswa
        student_col = df_answers.columns[0]
        question_cols = [col for col in df_answers.columns if col != student_col]
        
        # Ekstrak kunci jawaban
        key_answers = {}
        for col in question_cols:
            key_answers[col] = df_key[col].iloc[0]
    
    return df_answers, key_answers if df_key is not None else None

# Fungsi untuk menilai jawaban
def evaluate_answers(df_answers, key_answers, student_col):
    question_cols = [col for col in df_answers.columns if col != student_col]
    
    # Inisialisasi dataframe hasil
    results = pd.DataFrame(index=df_answers.index)
    results[student_col] = df_answers[student_col]
    
    # Hitung jawaban benar/salah
    for col in question_cols:
        results[f"{col}_correct"] = (df_answers[col] == key_answers[col]).astype(int)
    
    # Hitung nilai total siswa
    score_columns = [col for col in results.columns if col.endswith('_correct')]
    results['total_correct'] = results[score_columns].sum(axis=1)
    results['score'] = (results['total_correct'] / len(question_cols)) * 100
    
    return results

# Fungsi untuk menganalisis kesulitan soal
def analyze_difficulty(results, question_cols):
    difficulty = {}
    for col in question_cols:
        col_result = f"{col}_correct"
        if col_result in results.columns:
            correct_rate = results[col_result].mean() * 100
            difficulty[col] = {
                'correct_rate': correct_rate,
                'difficulty_level': get_difficulty_level(correct_rate)
            }
    return difficulty

# Fungsi untuk menentukan level kesulitan
def get_difficulty_level(correct_rate):
    if correct_rate < 30:
        return "Sangat Sulit"
    elif correct_rate < 50:
        return "Sulit"
    elif correct_rate < 70:
        return "Sedang"
    elif correct_rate < 90:
        return "Mudah"
    else:
        return "Sangat Mudah"
        
# Fungsi mengambil status
def highlight_status(row):
    if row['Status'] == 'Lulus':
        return ['background-color: #E8F5E9'] * len(row)
    else:
        return ['background-color: #FFEBEE'] * len(row)

# Fungsi untuk membuat rekomendasi topik
def generate_topic_recommendations(difficulty_data, topic_mapping=None):
    recommendations = []
    
    # Jika tidak ada pemetaan topik, gunakan soal secara langsung
    if topic_mapping is None:
        topic_mapping = {q: f"Materi pada {q}" for q in difficulty_data.keys()}
    
    for question, data in difficulty_data.items():
        if data['correct_rate'] < 50:
            if question in topic_mapping:
                topic = topic_mapping[question]
                recommendations.append({
                    'question': question,
                    'topic': topic,
                    'correct_rate': data['correct_rate'],
                    'recommendation': f"Perlu review pada topik '{topic}'"
                })
            else:
                recommendations.append({
                    'question': question,
                    'topic': f"Materi pada {question}",
                    'correct_rate': data['correct_rate'],
                    'recommendation': f"Perlu review pada materi di {question}"
                })
    
    return recommendations

# Halaman Utama
def main():
    st.markdown('<div class="main-header">📊 Analisis Hasil Ujian</div>', unsafe_allow_html=True)
    st.markdown(""" By Doyahudin""")
    st.markdown("""
    Aplikasi ini membantu guru menganalisis hasil ujian siswa untuk:
    - Mengidentifikasi soal-soal tersulit
    - Melihat rata-rata nilai kelas
    - Mendeteksi topik yang perlu remedial
    - Memetakan kesenjangan belajar
    """)
    
    # Sidebar untuk Upload dan Konfigurasi
    with st.sidebar:
        st.header("Unggah Data")
        
        # Pilihan cara input data
        input_method = st.radio(
            "Pilih cara input data:",
            ("Unggah File Excel", "Unggah File CSV", "Input Manual (Coming Soon)")
        )
        
        uploaded_file = None
        key_file = None
        
        if input_method == "Unggah File Excel":
            uploaded_file = st.file_uploader("Unggah file hasil ujian (.xlsx)", type=["xlsx"])
            
            # Opsi untuk kunci jawaban
            key_option = st.radio(
                "Kunci jawaban:",
                ("Baris pertama adalah kunci", "Unggah file kunci terpisah", "Input manual")
            )
            
            if key_option == "Unggah file kunci terpisah":
                key_file = st.file_uploader("Unggah file kunci jawaban (.xlsx)", type=["xlsx"])
            elif key_option == "Input manual":
                st.info("Fitur input manual kunci jawaban akan segera hadir.")
                
        elif input_method == "Unggah File CSV":
            uploaded_file = st.file_uploader("Unggah file hasil ujian (.csv)", type=["csv"])
            
            # Opsi untuk kunci jawaban
            key_option = st.radio(
                "Kunci jawaban:",
                ("Baris pertama adalah kunci", "Unggah file kunci terpisah", "Input manual")
            )
            
            if key_option == "Unggah file kunci terpisah":
                key_file = st.file_uploader("Unggah file kunci jawaban (.csv)", type=["csv"])
            elif key_option == "Input manual":
                st.info("Fitur input manual kunci jawaban akan segera hadir.")
        
        # Konfigurasi tambahan
        st.header("Konfigurasi")
        student_col_name = st.text_input("Nama kolom untuk nama siswa:", "Nama")
        pass_threshold = st.slider("Batas nilai kelulusan:", 0, 100, 70)
        
    # Main Content
    if uploaded_file is not None:
        # Baca file yang diunggah
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df_answers = pd.read_excel(uploaded_file)
            else:
                df_answers = pd.read_csv(uploaded_file)
                
            # Tampilkan data yang diunggah
            st.markdown('<div class="sub-header">Data Hasil Ujian</div>', unsafe_allow_html=True)
            st.dataframe(df_answers, use_container_width=True)
            
            # Baca file kunci jawaban jika ada
            df_key = None
            if key_file is not None:
                if key_file.name.endswith('.xlsx'):
                    df_key = pd.read_excel(key_file)
                else:
                    df_key = pd.read_csv(key_file)
                st.markdown('<div class="sub-header">Data Kunci Jawaban</div>', unsafe_allow_html=True)
                st.dataframe(df_key, use_container_width=True)
            
            # Preprocessing data
            has_key_column = key_option == "Baris pertama adalah kunci"
            df_answers, key_answers = preprocess_data(df_answers, df_key, has_key_column)
            
            if key_answers:
                # Analisis hasil
                results = evaluate_answers(df_answers, key_answers, student_col_name)
                
                # Dapatkan kolom soal
                question_cols = [col for col in df_answers.columns if col != student_col_name]
                
                # Analisis kesulitan soal
                difficulty_data = analyze_difficulty(results, question_cols)
                
                # Tampilkan hasil analisis
                st.markdown('<div class="sub-header">Hasil Analisis</div>', unsafe_allow_html=True)
                
                # Layout dengan kolom
                col1, col2 = st.columns(2)
                
                with col1:
                    # Menampilkan statistik dasar
                    avg_score = results['score'].mean()
                    median_score = results['score'].median()
                    min_score = results['score'].min()
                    max_score = results['score'].max()
                    pass_rate = (results['score'] >= pass_threshold).mean() * 100
                    
                    st.markdown('<div class="insight-card">', unsafe_allow_html=True)
                    st.markdown(f"### Statistik Nilai Kelas")
                    st.markdown(f"**Nilai Rata-rata**: {avg_score:.2f}")
                    st.markdown(f"**Nilai Tengah**: {median_score:.2f}")
                    st.markdown(f"**Nilai Minimum**: {min_score:.2f}")
                    st.markdown(f"**Nilai Maksimum**: {max_score:.2f}")
                    st.markdown(f"**Persentase Kelulusan**: {pass_rate:.2f}% (Batas {pass_threshold})")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Grafik distribusi nilai
                    st.markdown("### Distribusi Nilai")
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.histplot(results['score'], bins=10, kde=True, ax=ax)
                    ax.axvline(x=pass_threshold, color='red', linestyle='--', label=f'Batas Lulus ({pass_threshold})')
                    ax.set_xlabel('Nilai')
                    ax.set_ylabel('Jumlah Siswa')
                    ax.legend()
                    st.pyplot(fig)
                    
                with col2:
                    # Soal tersulit
                    st.markdown("### Analisis Tingkat Kesulitan Soal")
                    
                    # Konversi difficulty_data ke DataFrame untuk tampilan yang lebih baik
                    difficulty_df = pd.DataFrame([
                        {
                            'Soal': q,
                            'Persentase Benar': f"{data['correct_rate']:.2f}%",
                            'Tingkat Kesulitan': data['difficulty_level']
                        }
                        for q, data in difficulty_data.items()
                    ])
                    
                    # Urutkan berdasarkan tingkat kesulitan (persentase benar paling rendah)
                    difficulty_df = difficulty_df.sort_values(by='Persentase Benar')
                    
                    # Tampilkan tabel
                    st.dataframe(difficulty_df, use_container_width=True)
                    
                    # Grafik tingkat kesulitan soal
                    st.markdown("### Grafik Tingkat Kesulitan Soal")
                    difficulty_data_sorted = {k: v for k, v in sorted(difficulty_data.items(), key=lambda item: item[1]['correct_rate'])}
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    questions = list(difficulty_data_sorted.keys())
                    correct_rates = [data['correct_rate'] for data in difficulty_data_sorted.values()]
                    
                    colors = ['#D32F2F' if rate < 50 else '#388E3C' for rate in correct_rates]
                    
                    bars = ax.bar(questions, correct_rates, color=colors)
                    ax.set_ylabel('Persentase Jawaban Benar (%)')
                    ax.set_xlabel('Soal')
                    ax.set_ylim(0, 100)
                    ax.axhline(y=50, color='gray', linestyle='--', alpha=0.7)
                    
                    # Rotasi label sumbu x jika terlalu banyak soal
                    if len(questions) > 5:
                        plt.xticks(rotation=45, ha='right')
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                
                # Rekomendasi topik remedial
                st.markdown('<div class="sub-header">Rekomendasi Topik Remedial</div>', unsafe_allow_html=True)
                recommendations = generate_topic_recommendations(difficulty_data)
                
                if recommendations:
                    recom_df = pd.DataFrame(recommendations)
                    st.dataframe(recom_df[['question', 'correct_rate', 'recommendation']], use_container_width=True)
                    
                    st.markdown('<div class="insight-card">', unsafe_allow_html=True)
                    st.markdown("### Kesimpulan AI")
                    
                    # Hitung jumlah topik yang perlu remedial
                    remedial_count = len(recommendations)
                    total_questions = len(question_cols)
                    remedial_percentage = (remedial_count / total_questions) * 100
                    
                    if remedial_percentage > 50:
                        st.markdown(f"<p><span class='highlight'>⚠️ {remedial_percentage:.1f}% soal memiliki tingkat keberhasilan rendah.</span> Sebaiknya lakukan remedial komprehensif untuk materi pada bab ini.</p>", unsafe_allow_html=True)
                    elif remedial_percentage > 30:
                        st.markdown(f"<p><span class='highlight'>⚠️ {remedial_percentage:.1f}% soal memiliki tingkat keberhasilan rendah.</span> Fokus pada topik-topik yang diidentifikasi di atas untuk remedial.</p>", unsafe_allow_html=True)
                    elif remedial_percentage > 0:
                        st.markdown(f"<p>🔍 {remedial_percentage:.1f}% soal memiliki tingkat keberhasilan rendah. Berikan penekanan lebih pada topik-topik tersebut pada pertemuan berikutnya.</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<p><span class='success'>✅ Semua soal memiliki tingkat keberhasilan yang baik.</span> Lanjutkan ke materi berikutnya.</p>", unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="insight-card">', unsafe_allow_html=True)
                    st.markdown("<p><span class='success'>✅ Tidak ada topik yang perlu remedial. Siswa telah menguasai semua materi dengan baik.</span></p>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Hasil per siswa
                st.markdown('<div class="sub-header">Hasil Per Siswa</div>', unsafe_allow_html=True)
                student_results = results[[student_col_name, 'total_correct', 'score']].copy()
                student_results.columns = ['Nama Siswa', 'Jumlah Benar', 'Nilai']
                student_results['Status'] = student_results['Nilai'].apply(lambda x: 'Lulus' if x >= pass_threshold else 'Tidak Lulus')
                student_results = student_results.sort_values(by='Nilai', ascending=False)
                
                st.dataframe(
                    student_results.style.apply(highlight_status, axis=1),
                    use_container_width=True
                )
                
                # Download hasil analisis
                st.markdown('<div class="sub-header">Download Hasil Analisis</div>', unsafe_allow_html=True)
                
                st.markdown(download_link(student_results, 'hasil_siswa.csv', 'Download Hasil Per Siswa (CSV)'), unsafe_allow_html=True)
                st.markdown(download_link(difficulty_df, 'analisis_soal.csv', 'Download Analisis Soal (CSV)'), unsafe_allow_html=True)
                
                if recommendations:
                    st.markdown(download_link(recom_df, 'rekomendasi_remedial.csv', 'Download Rekomendasi Remedial (CSV)'), unsafe_allow_html=True)
                
            else:
                st.error("Terjadi masalah dalam memproses kunci jawaban. Pastikan format kunci jawaban sesuai.")
                
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")
            st.info("Pastikan format file sesuai. File harus memiliki kolom untuk nama siswa dan kolom untuk setiap soal ujian.")
    else:
        # Tampilkan panduan dan contoh format data
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown("### Panduan Penggunaan")
        
        st.markdown("""
        1. **Persiapkan data** dalam format Excel atau CSV dengan struktur:
           - Kolom pertama: Nama siswa
           - Kolom lainnya: Jawaban siswa untuk setiap soal
           
        2. **Unggah file** hasil ujian melalui panel di sidebar
        
        3. **Pilih sumber kunci jawaban**:
           - Baris pertama adalah kunci
           - Unggah file kunci terpisah
           - Input manual (segera hadir)
           
        4. **Lihat analisis** yang mencakup:
           - Statistik nilai kelas
           - Distribusi nilai
           - Analisis tingkat kesulitan soal
           - Rekomendasi topik remedial
           - Hasil per siswa
        """)
        
        st.markdown("### Contoh Format Data")
        
        # Contoh data
        example_data = {
            'Nama': ['KUNCI', 'Siswa 1', 'Siswa 2', 'Siswa 3', 'Siswa 4', 'Siswa 5'],
            'Soal 1': ['A', 'A', 'B', 'A', 'C', 'A'],
            'Soal 2': ['B', 'B', 'B', 'A', 'B', 'C'],
            'Soal 3': ['C', 'C', 'A', 'C', 'B', 'C'],
            'Soal 4': ['A', 'D', 'A', 'A', 'A', 'B'],
            'Soal 5': ['D', 'D', 'D', 'C', 'D', 'D']
        }
        
        example_df = pd.DataFrame(example_data)
        st.dataframe(example_df, use_container_width=True)
        st.markdown("*Catatan: Dalam contoh di atas, baris pertama adalah kunci jawaban.*")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Demo dengan data contoh
        st.markdown('<div class="sub-header">Coba Demo</div>', unsafe_allow_html=True)
        if st.button("Lihat Demo dengan Data Contoh"):
            # Convert example dataframe to CSV for demo
            demo_file = BytesIO()
            example_df.to_csv(demo_file, index=False)
            demo_file.seek(0)
            
            # Use the demo file
            df_answers = pd.read_csv(demo_file)
            
            # Tampilkan data contoh
            st.markdown('<div class="sub-header">Data Hasil Ujian Demo</div>', unsafe_allow_html=True)
            st.dataframe(df_answers, use_container_width=True)
            
            # Preprocessing data demo
            df_answers, key_answers = preprocess_data(df_answers, None, True)
            
            # Lakukan analisis
            student_col_name = "Nama"
            results = evaluate_answers(df_answers, key_answers, student_col_name)
            
            # Dapatkan kolom soal
            question_cols = [col for col in df_answers.columns if col != student_col_name]
            
            # Analisis kesulitan soal
            difficulty_data = analyze_difficulty(results, question_cols)
            
            # Tampilkan hasil analisis demo
            st.markdown('<div class="sub-header">Hasil Analisis Demo</div>', unsafe_allow_html=True)
            
            # Layout dengan kolom
            col1, col2 = st.columns(2)
            
            with col1:
                # Menampilkan statistik dasar
                avg_score = results['score'].mean()
                median_score = results['score'].median()
                min_score = results['score'].min()
                max_score = results['score'].max()
                pass_threshold = 70
                pass_rate = (results['score'] >= pass_threshold).mean() * 100
                
                st.markdown('<div class="insight-card">', unsafe_allow_html=True)
                st.markdown(f"### Statistik Nilai Kelas")
                st.markdown(f"**Nilai Rata-rata**: {avg_score:.2f}")
                st.markdown(f"**Nilai Tengah**: {median_score:.2f}")
                st.markdown(f"**Nilai Minimum**: {min_score:.2f}")
                st.markdown(f"**Nilai Maksimum**: {max_score:.2f}")
                st.markdown(f"**Persentase Kelulusan**: {pass_rate:.2f}% (Batas {pass_threshold})")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Grafik distribusi nilai
                st.markdown("### Distribusi Nilai")
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.histplot(results['score'], bins=10, kde=True, ax=ax)
                ax.axvline(x=pass_threshold, color='red', linestyle='--', label=f'Batas Lulus ({pass_threshold})')
                ax.set_xlabel('Nilai')
                ax.set_ylabel('Jumlah Siswa')
                ax.legend()
                st.pyplot(fig)
                
            with col2:
                # Soal tersulit
                st.markdown("### Analisis Tingkat Kesulitan Soal")
                
                # Konversi difficulty_data ke DataFrame untuk tampilan yang lebih baik
                difficulty_df = pd.DataFrame([
                    {
                        'Soal': q,
                        'Persentase Benar': f"{data['correct_rate']:.2f}%",
                        'Tingkat Kesulitan': data['difficulty_level']
                    }
                    for q, data in difficulty_data.items()
                ])
                
                # Urutkan berdasarkan tingkat kesulitan (persentase benar paling rendah)
                difficulty_df = difficulty_df.sort_values(by='Persentase Benar')
                
                # Tampilkan tabel
                st.dataframe(difficulty_df, use_container_width=True)
                
                # Grafik tingkat kesulitan soal
                st.markdown("### Grafik Tingkat Kesulitan Soal")
                difficulty_data_sorted = {k: v for k, v in sorted(difficulty_data.items(), key=lambda item: item[1]['correct_rate'])}
                
                fig, ax = plt.subplots(figsize=(10, 6))
                questions = list(difficulty_data_sorted.keys())
                correct_rates = [data['correct_rate'] for data in difficulty_data_sorted.values()]
                
                colors = ['#D32F2F' if rate < 50 else '#388E3C' for rate in correct_rates]
                
                bars = ax.bar(questions, correct_rates, color=colors)
                ax.set_ylabel('Persentase Jawaban Benar (%)')
                ax.set_xlabel('Soal')
                ax.set_ylim(0, 100)
                ax.axhline(y=50, color='gray', linestyle='--', alpha=0.7)
                
                plt.tight_layout()
                st.pyplot(fig)

if __name__ == "__main__":
    main()
