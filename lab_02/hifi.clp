
;;;======================================================
;;;   Wine Expert Sample Problem
;;;
;;;     WINEX: The WINe EXpert system.
;;;     This example selects an appropriate wine
;;;     to drink with a meal.
;;;
;;;     CLIPS Version 6.4 Example
;;;
;;;     To execute, merely load, reset and run.
;;;======================================================

(defmodule MAIN (export ?ALL))

;;****************
;;* DEFFUNCTIONS *
;;****************

(deffunction MAIN::ask-question (?question ?allowed-values)
   (print ?question)
   (bind ?answer (read))
   (if (lexemep ?answer) then (bind ?answer (lowcase ?answer)))
   (while (not (member$ ?answer ?allowed-values)) do
      (print ?question)
      (bind ?answer (read))
      (if (lexemep ?answer) then (bind ?answer (lowcase ?answer))))
   ?answer)

;;*****************
;;* INITIAL STATE *
;;*****************

(deftemplate MAIN::attribute
   (slot name)
   (slot value)
   (slot certainty (default 100.0)))

(defrule MAIN::start
  (declare (salience 10000))
  =>
  (set-fact-duplication TRUE)
  (focus QUESTIONS FINDATTRS SPEAKERS PRINT-RESULTS))

(defrule MAIN::combine-certainties ""
  (declare (salience 100)
           (auto-focus TRUE))
  ?rem1 <- (attribute (name ?rel) (value ?val) (certainty ?per1))
  ?rem2 <- (attribute (name ?rel) (value ?val) (certainty ?per2))
  (test (neq ?rem1 ?rem2))
  =>
  (retract ?rem1)
  (modify ?rem2 (certainty (/ (- (* 100 (+ ?per1 ?per2)) (* ?per1 ?per2)) 100))))
  
;;******************
;;* QUESTION RULES *
;;******************

(defmodule QUESTIONS (import MAIN ?ALL) (export ?ALL))

(deftemplate QUESTIONS::question
   (slot attribute (default ?NONE))
   (slot the-question (default ?NONE))
   (multislot valid-answers (default ?NONE))
   (slot already-asked (default FALSE))
   (multislot precursors (default ?DERIVE)))
   
(defrule QUESTIONS::ask-a-question
   ?f <- (question (already-asked FALSE)
                   (precursors)
                   (the-question ?the-question)
                   (attribute ?the-attribute)
                   (valid-answers $?valid-answers))
   =>
   (modify ?f (already-asked TRUE))
   (assert (attribute (name ?the-attribute)
                      (value (ask-question ?the-question ?valid-answers)))))

(defrule QUESTIONS::precursor-is-satisfied
   ?f <- (question (already-asked FALSE)
                   (precursors ?name is ?value $?rest))
         (attribute (name ?name) (value ?value))
   =>
   (if (eq (nth$ 1 ?rest) and) 
    then (modify ?f (precursors (rest$ ?rest)))
    else (modify ?f (precursors ?rest))))

(defrule QUESTIONS::precursor-is-not-satisfied
   ?f <- (question (already-asked FALSE)
                   (precursors ?name is-not ?value $?rest))
         (attribute (name ?name) (value ~?value))
   =>
   (if (eq (nth$ 1 ?rest) and) 
    then (modify ?f (precursors (rest$ ?rest)))
    else (modify ?f (precursors ?rest))))

;;*******************
;;* WINEX QUESTIONS *
;;*******************

(defmodule SPEAKERS-QUESTIONS (import QUESTIONS ?ALL))

(deffacts SPEAKERS-QUESTIONS::question-attributes
  (question (attribute main-purpose)
            (the-question "Will you speakers be used for personal or business? ")
            (valid-answers personal business unknown))
  (question (attribute business-purpose)
            (precursors main-purpose is business)
            (the-question "What kind of business - studio, restaurant or concert? ")
            (valid-answers studio restaurant concert unknown))
  (question (attribute personal-purpose)
            (precursors main-purpose is personal)
            (the-question "What will be the usage for your speakers - home, cinema or computer? ")
            (valid-answers home cinema computer unknown))
  (question (attribute main-budget)
            (the-question "What is the budget level - low, average or high? ")
            (valid-answers low average high unknown))
  (question (attribute has-bt)
            ; (precursors main-purpose is personal)
            (the-question "Do you need BT connection? ")
            (valid-answers yes no unknown))
  (question (attribute is-hifi)
            (the-question "Should it be a HiRes music? ")
            (valid-answers yes no unknown))
 )
;;******************
;; The RULES module
;;******************

(defmodule RULES (import MAIN ?ALL) (export ?ALL))

(deftemplate RULES::rule
  (slot certainty (default 100.0))
  (multislot if)
  (multislot then))

(defrule RULES::throw-away-ands-in-antecedent
  ?f <- (rule (if and $?rest))
  =>
  (modify ?f (if ?rest)))

(defrule RULES::throw-away-ands-in-consequent
  ?f <- (rule (then and $?rest))
  =>
  (modify ?f (then ?rest)))

(defrule RULES::remove-is-condition-when-satisfied
  ?f <- (rule (certainty ?c1) 
              (if ?attribute is ?value $?rest))
  (attribute (name ?attribute) 
             (value ?value) 
             (certainty ?c2))
  =>
  (modify ?f (certainty (min ?c1 ?c2)) (if ?rest)))

(defrule RULES::remove-is-not-condition-when-satisfied
  ?f <- (rule (certainty ?c1) 
              (if ?attribute is-not ?value $?rest))
  (attribute (name ?attribute) (value ~?value) (certainty ?c2))
  =>
  (modify ?f (certainty (min ?c1 ?c2)) (if ?rest)))

(defrule RULES::perform-rule-consequent-with-certainty
  ?f <- (rule (certainty ?c1) 
              (if) 
              (then ?attribute is ?value with certainty ?c2 $?rest))
  =>
  (modify ?f (then ?rest))
  (assert (attribute (name ?attribute) 
                     (value ?value)
                     (certainty (/ (* ?c1 ?c2) 100)))))

(defrule RULES::perform-rule-consequent-without-certainty
  ?f <- (rule (certainty ?c1)
              (if)
              (then ?attribute is ?value $?rest))
  (test (or (eq (length$ ?rest) 0)
            (neq (nth$ 1 ?rest) with)))
  =>
  (modify ?f (then ?rest))
  (assert (attribute (name ?attribute) (value ?value) (certainty ?c1))))

;;*******************************
;;* CHOOSE RULES *
;;*******************************

(defmodule FINDATTRS (import RULES ?ALL)
                            (import QUESTIONS ?ALL)
                            (import MAIN ?ALL))

(defrule FINDATTRS::startit => (focus RULES))

(deffacts the-speakers-rules

  ; Rules for picking the best purpose

  (rule (if main-purpose is business and business-purpose is concert)
        (then best-purpose is concert with certainty 75 and 
              best-purpose is restaurant with certainty 20 and
              best-purpose is studio with certainty 5
              ))

  (rule (if main-purpose is business and business-purpose is restaurant)
        (then best-purpose is concert with certainty 5 and 
              best-purpose is restaurant with certainty 75 and
              best-purpose is studio with certainty 20
              ))

  (rule (if main-purpose is business and business-purpose is studio)
        (then best-purpose is concert with certainty 10 and 
              best-purpose is studio with certainty 80 and
              best-purpose is restaurant with certainty 10
              ))

  (rule (if main-purpose is personal and personal-purpose is home)
        (then best-purpose is home with certainty 75 and 
              best-purpose is cinema with certainty 20 and
              best-purpose is computer with certainty 5
              ))

  (rule (if main-purpose is personal and personal-purpose is cinema)
        (then best-purpose is cinema with certainty 60 and 
              best-purpose is home with certainty 20 and
              best-purpose is studio with certainty 15 and
              best-purpose is computer with certainty 5
              ))
  
  (rule (if main-purpose is personal and personal-purpose is computer)
        (then best-purpose is computer with certainty 70 and 
              best-purpose is cinema with certainty 10 and
              best-purpose is home with certainty 20
              ))
  
  ; Rules for picking the best sound
  (rule (if is-hifi is yes)
        (then best-hifi is yes with certainty 70 and best-hifi is no with certainty 30)
        )
  (rule (if is-hifi is no)
        (then best-hifi is yes with certainty 30 and best-hifi is no with certainty 70)
        )
  ; Rules for picking the best connectivity
  (rule (if has-bt is yes)
        (then best-bt is yes with certainty 60 and best-bt is no with certainty 40)
        )
  (rule (if has-bt is no)
        (then best-bt is yes with certainty 40 and best-bt is no with certainty 60)
        )

  ; Rules for picking an applicable budget
  (rule (if main-budget is low)
        (then best-budget is low with certainty 60 and
              best-budget is average with certainty 30 and
              best-budget is high with certainty 10
              ))
  (rule (if main-budget is average)
        (then best-budget is low with certainty 10 and
              best-budget is average with certainty 70 and
              best-budget is high with certainty 20
              ))
  (rule (if main-budget is high)
        (then best-budget is low with certainty 10 and
              best-budget is average with certainty 30 and
              best-budget is high with certainty 60
              ))
)

;;************************
;;* WINE SELECTION RULES *
;;************************

(defmodule SPEAKERS (import MAIN ?ALL))

(deffacts any-attributes
  (attribute (name best-purpose) (value any))
  (attribute (name best-hifi) (value any))
  (attribute (name best-bt) (value any))
  (attribute (name best-budget) (value any))
)

(deftemplate SPEAKERS::speaker
  (slot name (default ?NONE))
  (multislot purpose (default any))
  (multislot hifi (default any))
  (multislot bt (default any))
  (multislot budget (default any))
)

(deffacts SPEAKERS::the-speakers-list 
  ; big ones
  (speaker (name Edifier-AirPulse-A300_2_0) (purpose concert restaurant) (hifi yes) (bt yes) (budget high))
  (speaker (name Edifier-AirPulse-A80_2_0) (purpose concert restaurant studio) (hifi no) (bt no) (budget average low))
  ; avg
  (speaker (name Edifier-R2850DB_2_0) (purpose studio restaurant home cinema) (hifi no) (bt yes) (budget high average))
  (speaker (name Edifier-R2750DB_2_0) (purpose studio restaurant home cinema) (hifi no) (bt yes) (budget average))
  (speaker (name Edifier-R1280DB_2_0) (purpose studio home computer) (hifi no) (bt yes) (budget average low))
  (speaker (name Edifier-S880DB_2_0) (purpose studio home computer) (hifi yes) (bt yes) (budget high average))
  (speaker (name Edifier-S360DB_3_1) (purpose studio home cinema) (hifi yes) (bt yes) (budget high))
  (speaker (name Edifier-S351DB_3_1) (purpose studio home cinema) (hifi yes) (bt yes) (budget high average))
  ; small
  (speaker (name Edifier-QD35_1_0) (purpose home) (hifi yes) (bt yes) (budget average))
  (speaker (name Edifier-R980T_2_0) (purpose home computer) (hifi no) (bt no) (budget low))
  (speaker (name Edifier-M1250_2_0) (purpose computer) (hifi no) (bt no) (budget low))
)
  
(defrule SPEAKERS::generate-speakers
  (speaker (name ?name)
        (purpose $? ?p $?)
        (hifi $? ?h $?)
        (bt $? ?b $?)
        (budget $? ?g $?))
  (attribute (name best-purpose) (value ?p) (certainty ?certainty-1))
  (attribute (name best-hifi) (value ?h) (certainty ?certainty-2))
  (attribute (name best-bt) (value ?b) (certainty ?certainty-3))
  (attribute (name best-budget) (value ?g) (certainty ?certainty-4))
  =>
  (assert (attribute (name speaker) (value ?name)
                     (certainty (min ?certainty-1 ?certainty-2 ?certainty-3 ?certainty-4)))))

;;*****************************
;;* PRINT SELECTED WINE RULES *
;;*****************************

(defmodule PRINT-RESULTS (import MAIN ?ALL))

(defrule PRINT-RESULTS::header ""
   (declare (salience 10))
   =>
   (println)
   (println " PROPOSED SPEAKER SYSTEMS" crlf)
   (println " SPEAKERS                  CERTAINTY")
   (println " -------------------------------")
   (assert (phase print-speakers)))

(defrule PRINT-RESULTS::print-speaker ""
  ?rem <- (attribute (name speaker) (value ?name) (certainty ?per))		  
  (not (attribute (name speaker) (certainty ?per1&:(> ?per1 ?per))))
  =>
  (retract ?rem)
  (format t " %-24s %2d%%%n" ?name ?per))

(defrule PRINT-RESULTS::remove-poor-choices ""
  ?rem <- (attribute (name speaker) (certainty ?per&:(< ?per 20)))
  =>
  (retract ?rem))

(defrule PRINT-RESULTS::end-spaces ""
   (not (attribute (name speaker)))
   =>
   (println))
