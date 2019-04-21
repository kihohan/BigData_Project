install.packages("foreign")
install.packages("dplyr")
install.packages("ggplot2")
install.packages("readx1")
install.packages("reshape")

library(ggplot2)
library(readxl)
library(dplyr)
library(reshape)

firestation <- read.csv("/Users/hankiho/Desktop/Data/전국 119안전센터 현황.csv", na = "-", fileEncoding = "CP949", encoding = "UTF-8", stringsAsFactors=TRUE) #윈도우에는 되고 맥에서안될떄 쓰는 코드
seoul_firestation <- firestation %>% 
                         select(시도본부,주소) %>% 
                         filter(시도본부 == "서울소방재난본부")
View(seoul_firestation)
시군구 <- substr(seoul_firestation$주소,6,9)
View(시군구)
firestation_count <- table(시군구)
View(firestation_count)
firestation_count <- rename(firestation_count, 소방서갯수 = Freq)
View(firestation_count) 


########################### 0. 공장 정보 데이터 정리.xlsx ############################



factory <- read_excel("0. 공장 정보 데이터 정리.xlsx")
View(factory)

new_factory <- factory %>% 
  select(시도,시군구,종업원수,용지면적,업종분류)

seoul_factory<- new_factory %>%
  filter(시도 == "서울특별시")
View(seoul_factory)

####공장 갯수 파악####
seoul_factory_count <- seoul_factory %>% 
                             group_by(시군구) %>% 
                             summarise(공장수 = n())
View(seoul_factory_count)
####시군구 별  종업원수 평균####
seoul_factory_people_count <- seoul_factory %>% 
                                   group_by(시군구) %>% 
                                   summarise(종업원수 = mean(종업원수))
View(seoul_factory_people_count)

####시군구 별 용지면적 평균####
seoul_factory_area <- seoul_factory %>% 
                                  group_by(시군구) %>% 
                                  summarise(용지면적 = mean(용지면적))
 
View(seoul_factory_area)
####시군구별 업종 별 가중치####
seoul_factory$weight <- ifelse(seoul_factory$'업종분류' == "10 식료품 제조업" |
                                 seoul_factory$'업종분류' ==  "11 음료 제조업",0.15,
                                    
                                    ifelse(seoul_factory$'업종분류' =="12 담배 제조업" | 
                                             seoul_factory$'업종분류' =="13 섬유제품 제조업(의복제외)"| 
                                             seoul_factory$'업종분류' =="14 의복,의복엑세서리 및 모피제품 제조업" | 
                                             seoul_factory$'업종분류' =="15 가죽,가방 및 신발 제조업" | 
                                             seoul_factory$'업종분류' =="16 목재 및 나무제품 제조업(가구제외)" | 
                                             seoul_factory$'업종분류' =="17 펄프,종이 및 종이제품 제조업" | 
                                             seoul_factory$'업종분류' =="18 인쇄 및 기록매체 복제업" | 
                                             seoul_factory$'업종분류' =="32 가구 제조업", 0.1,
                                           
                                           ifelse(seoul_factory$'업종분류' =="19 코크스,연탄 및 석유정제품 제조업" | 
                                                    seoul_factory$'업종분류' =="20 화학물질 및 화학제품 제조업(의약품제외)" | 
                                                    seoul_factory$'업종분류' =="21 의료용물질 및 의약품 제조업", 0.25,
                                                  
                                                  ifelse(seoul_factory$'업종분류' =="22 고무제품 및 플라스틱 제조업" | 
                                                           seoul_factory$'업종분류' =="23 비금속 광물제품 제조업" | 
                                                           seoul_factory$'업종분류' =="24 1차금속 제조업" | 
                                                           seoul_factory$'업종분류' =="25 금속가공제품 제조업(기계 및 가구제외)", 0.2,
                                                         
                                                         ifelse(seoul_factory$'업종분류' =="26 전자부품,컴퓨터,영상,음향 및 통신장비 제조업" | 
                                                                  seoul_factory$'업종분류' =="27 의료,정밀,광학기기 및 시계제조업" | 
                                                                  seoul_factory$'업종분류' =="28 전기장비 제조업" | 
                                                                  seoul_factory$'업종분류' =="29 기타 기계 및 장비 제조업" | 
                                                                  seoul_factory$'업종분류' =="30 자동차 및 트레일러 제조업" | 
                                                                  seoul_factory$'업종분류' =="31 기타 운송장비 제조업" | 
                                                                  seoul_factory$'업종분류' =="34 산업용 기계 및 장비 수리업" | 
                                                                  seoul_factory$'업종분류' =="33 기타제품 제조업", 0.3, 1)))))                                    
seoul_factory_point <- seoul_factory %>%
  group_by(시군구, weight) %>%
  summarise(count = n()) %>%
  mutate(total = weight * count) %>%
  mutate(업종별점수 = sum(total)) %>% 
  select(시군구,업종별점수)
View(seoul_factory_point)                                            
seoul_factory_point <- unique(seoul_factory_point)
View(seoul_factory_point)

####4가지 지수 구하기####
total <- read_excel("total.xlsx")
View(total)
total <- total %>% 
              mutate(인명피해지수 = (평균종업원수 / 평균용지면적)) %>% 
              mutate(골든타임지수 = (공장갯수 / 소방서갯수 )) %>% 
              mutate(재산피해지수 = 업종별점수) %>% 
              mutate(공장규모지수 = (평균용지면적) / mean(평균용지면적))
total_index<- total %>% 
                select(시군구,재산피해지수, 인명피해지수, 골든타임지수, 공장규모지수)
View(total_index)

###################################################표준정규화 하는 방법#########################################
total <- data.frame(total)
View(total)
scaled_total <- transform(total, 
                          소방서갯수 = scale(소방서갯수),
                          평균종업원수 = scale(평균종업원수),
                          평균용지면적 = scale(평균용지면적),
                          업종별점수 = scale(업종별점수),
                          공장갯수 = scale(공장갯수))
View(scaled_total)

##################################################[0,1] 정규화 하는 방법##############
scaled_total_index <- transform(total_index, 
                          재산피해지수 = (재산피해지수 - min(재산피해지수))/(max(재산피해지수) - min(재산피해지수)),
                          인명피해지수 = (인명피해지수 - min(인명피해지수))/(max(인명피해지수) - min(인명피해지수)),
                          골든타임지수 = (골든타임지수 - min(골든타임지수))/(max(골든타임지수) - min(골든타임지수)),
                          공장규모지수 = (공장규모지수 - min(공장규모지수))/(max(공장규모지수) - min(공장규모지수)))
View(scaled_total_index)                   
############################재산피해지수 + 인명피해지수 = 화재피해지수, 골든타임지수 + 공장규모지수 = 화재진압지연지수##############################
scaled_total_index %>% 
  mutate(화재피해지수 = 재산피해지수 + 인명피해지수) %>% 
  mutate(화재진압지연지수 = 골든타임지수 + 공장규모지수) %>% 
  select(시군구, 화재피해지수, 화재진압지연지수)
############################재산피해지수 + 인명피해지수 = 화재피해지수, 골든타임지수 + 공장규모지수 = 화재진압지연지수##############################
            
total_index_1 <- transform(total_index, 
                          재산피해지수 = scale(재산피해지수),
                          인명피해지수 = scale(인명피해지수),
                          골든타임지수 = scale(골든타임지수),
                          공장규모지수 = scale(공장규모지수))
View(total_index_1)
total_index_1 <- data.frame(total_index_1)
total_index_1 <- total_index_1 %>% 
  mutate(화재피해지수 = 재산피해지수 + 인명피해지수) %>% 
  mutate(화재진압지연지수 = 골든타임지수 + 공장규모지수) %>% 
  select(시군구, 화재피해지수, 화재진압지연지수)
###############################위에 에러뜸########################
write.csv(total_index_1, file = "total_index_1", row.names = FALSE)
final_index <- read.csv("total_index_1.csv")
real_final<- final_index %>% 
                  mutate(화재피해지수 = 재산피해지수 + 인명피해지수) %>% 
                  mutate(화재진압지연지수 = 골든타임지수 + 공장규모지수) %>% 
                  select(시군구, 화재피해지수, 화재진압지연지수)
View(real_final)
summary(real_final)

###############################그래프 그리기###################################

ggplot(data = real_final, aes(x = 화재피해지수, y = 화재진압지연지수)) +
  xlim(-0.8806,3.3654) +
  ylim(-0.9090,8.7295) +
  geom_point(shape=20, size=3, colour="blue") +
  ggtitle("산점도 그래프") +
  geom_hline(yintercept=50, colour="red", linetype = 2) +
  geom_vline(xintercept=50, colour="red", linetype = 2)  +
  theme_bw(base_family = "AppleGothic") 


