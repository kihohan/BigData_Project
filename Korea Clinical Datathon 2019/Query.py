#!/usr/bin/env python
# coding: utf-8

# In[ ]:


with main as (
SELECT distinct A.person_id, A.concept_id, B.gender_concept_id,  B.birth_datetime, X.condition_start_date,

case 
when C.dm_flag is not null then true
else false
end as dm_flag

,D.measurement_concept_id, D.measurement_datetime, E.concept_name, D.value_as_number,

case when F.death_date is not null then true else false end as death_flag,

case 
when G.ckd_flag is not null then true
else false
end as ckd_flag

FROM `korea-datathon-2019.team10.deep_neck_list` A

left outer join 
`chrome-coast-249308.korea_datathon_dataset.person`  B
on A.person_id = B.person_id


left outer join 
`chrome-coast-249308.korea_datathon_dataset.condition_occurrence`  X
on  A.person_id = X.person_id and A.concept_id = X.condition_concept_id 

left outer join
(
SELECT A.person_id as dm_flag FROM `korea-datathon-2019.team10.deep_neck_list` A, `korea-datathon-2019.team10.dm_list` B
where  A.person_id = B.person_id group by A.person_id 
) C on A.person_id = C.dm_flag

left outer join
`chrome-coast-249308.korea_datathon_dataset.measurement`  D
on A.person_id = D.person_id 

left outer join
`chrome-coast-249308.korea_datathon_dataset.concept`  E
on D.measurement_concept_id = E.concept_id

left outer join
`chrome-coast-249308.korea_datathon_dataset.death`  F
on D.person_id = F.person_id

left outer join
(
SELECT A.person_id as ckd_flag FROM `korea-datathon-2019.team10.deep_neck_list` A, `korea-datathon-2019.team10.ckd_list` B
where  A.person_id = B.person_id group by A.person_id 
) G on A.person_id = G.ckd_flag

where
      -- 동일 환자 멀티 진단이력 존재시, min(condition_start_datetime)으로 1건 추출
      X.condition_start_datetime = (select min(zz.condition_start_datetime) from `chrome-coast-249308.korea_datathon_dataset.condition_occurrence` zz 
                                    where zz.person_id = X.person_id and zz.condition_concept_id = X.condition_concept_id)
  -- lab 검사결과 관련 concept_id                                   
  and D.measurement_concept_id in (
                            select x.concept_id
                              from `korea-datathon-2019.team10.FEATURE_SELECTION` x
                             where x.feature_type = 'measure'                       
                            )
  -- 검사 시행시점은 최초 진단일 + 365일 이내 최초 시행이력 1건                            
  and D.measurement_datetime in (select min(y.measurement_datetime) from `chrome-coast-249308.korea_datathon_dataset.measurement` y 
                                where y.measurement_datetime between X.condition_start_datetime and datetime_add(x.condition_start_datetime, interval 365 day)                           
                                  and y.person_id = D.person_id
                                  and y.measurement_concept_id = D.measurement_concept_id
                              )
  -- 동일 환자/동일 진단일 서로 다른 Concept 진료 중복된 경우, min(concept_id)로 1건 추출                   
  and A.concept_id = (select min(yy.concept_id) from `korea-datathon-2019.team10.deep_neck_list` yy where yy.person_id = A.person_id)                            
)


select
      x.person_id,
      x.concept_id , x.gender_concept_id , x.birth_datetime , x.condition_start_date , x.dm_flag, x.ckd_flag, x.death_flag,
      max(if(x.measurement_concept_id = 3025315, x.value_as_number, null)) as weight,
      max(if(x.measurement_concept_id = 40758583, x.value_as_number, null)) as hgbA1c,      
      max(if(x.measurement_concept_id = 3015160, x.value_as_number, null)) as creatine,
      max(if(x.measurement_concept_id = 3023540, x.value_as_number, null)) as height,
      max(if(x.measurement_concept_id = 3002030, x.value_as_number, null)) as Lymphocytes,
      max(if(x.measurement_concept_id = 3019069, x.value_as_number, null)) as Monocytes,
      max(if(x.measurement_concept_id = 3006504, x.value_as_number, null)) as Eosinophils,
      max(if(x.measurement_concept_id = 3018010, x.value_as_number, null)) as Neutrophils,
      max(if(x.measurement_concept_id = 3020460, x.value_as_number, null)) as protein,
      max(if(x.measurement_concept_id = 3015183, x.value_as_number, null)) as ESR,
      max(if(x.measurement_concept_id = 4302666, x.value_as_number, null)) as bodytemp,
      max(if(x.measurement_concept_id = 3047181, x.value_as_number, null)) as Lactate,
      max(if(x.measurement_concept_id = 3010156, x.value_as_number, null)) as proteinHS,
      max(if(x.measurement_concept_id = 4015482, x.value_as_number, null)) as Ddimer,      
      max(if(x.measurement_concept_id = 3005347, x.value_as_number, null)) as ammonia
     
  from main x 
 group by x.person_id,x.concept_id , x.gender_concept_id , x.birth_datetime , x.condition_start_date , x.dm_flag, x.ckd_flag, x.death_flag
  --having count(x.person_id) > 1
  order by 1, 2

