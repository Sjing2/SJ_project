# BOK_Report_Analysis

#### 한국은행의 금융통화위원회 의사록을 분석을 통한 기준금리 예측

> [관련 논문]: Project_Reference/Deciphering Monetary Policy Board Minutes through Text Mining Approach.pdf



#### 활용 패키지

> `eKoNLPy`, `Scrapy`



#### 활용 데이터 Set(Data Crawling)

> 1. 한국은행 의사록
>
> 2. 금리 관련 뉴스 기사(연합뉴스, 연합 인포맥스, 이데일리)
>
> 3. 채권 분석 리포트



#### 데이터 전처리(Data Preprocessing)

>1. **NLP 분석을 위해 경제 특화된 eKoNLPy 이용**
>   * 관련 자료 : https://github.com/entelecheia/eKoNLPy
>
>2. **N-Gramize**
>
>   * 최대 5-Gram까지의 단어로 구성
>
>   * 전 처리 후 : 단어 2,712개 | N-Gram 73,824개 사용



#### 극성 분류(Data Analysis)

> `Naive Bayes Classifier` 이용

> $$
> polarity \ score = {p(feature|hawkish) \over p(feature|dovish)}
> $$
>
> - *Hawkish* : 10,594개
> - *Dovish* : 7974개



#### 의사록 어조 분석 결과

![image-20200907171049242](README.assets/image-20200907171049242.png)

