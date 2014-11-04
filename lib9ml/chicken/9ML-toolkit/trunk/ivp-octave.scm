;;
;;  NineML IVP code generator for Octave.
;;
;;
;; Copyright 2010-2012 Ivan Raikov and the Okinawa Institute of
;; Science and Technology.
;;
;; This program is free software: you can redistribute it and/or
;; modify it under the terms of the GNU General Public License as
;; published by the Free Software Foundation, either version 3 of the
;; License, or (at your option) any later version.
;;
;; This program is distributed in the hope that it will be useful, but
;; WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
;; General Public License for more details.
;;
;; A full copy of the GPL license can be found at
;; <http://www.gnu.org/licenses/>.
;;


(module 9ML-ivp-octave

	(ivp-octave)

	(import scheme chicken )

(import (only extras sprintf)
	(only files make-pathname pathname-directory pathname-file absolute-pathname? )
	(only data-structures conc alist-ref intersperse ->string)
	(only posix current-directory)
	(only srfi-1 filter list-index)
	(only srfi-13 string-concatenate))
(require-extension make datatype signal-diagram 9ML-eval setup-api)


(define nl "\n")


(define (octave-m ivp-id start ivar hvar dvars events ic imax log-path adir solver-path)

  (let* ((states (cons ivar dvars))
	 (parameters (filter (lambda (x) (not (member (car x) states))) ic)))

  `(,(sprintf "autoload (~S,~S);~%" (->string ivp-id) (make-pathname adir solver-path))
    ,(sprintf "~A;~%~%" ivp-id)
    
    ,(sprintf "~A_initial = struct(~A);~%~%" ivp-id
	      (string-concatenate
	       (intersperse
		(map (lambda (x)
		       (let ((n (car x)) (v (cdr x)))
			 (let ((v (if (boolean? v) (if v "true" "false") v)))
			   (sprintf "\"~A\",~A" n v))))
		     (cons (cons ivar start) ic))
		",")))

    ,(sprintf "i = 1; t = 0; tmax = ~A;~%" imax)
    ,(sprintf "~A_state = ~A_initial;~%" ivp-id ivp-id)
    ,(sprintf "data = [[~A]];~%" 
	      (string-concatenate (intersperse (map (lambda (s) (sprintf "~A_state.~A" ivp-id s)) states) ",") ))

    ,(sprintf "tic;~%")
    ,(sprintf "while (t < tmax) ~%")

    ,(sprintf "  y = ~A(~A_state);~%" ivp-id ivp-id)

    ,(if (null? events) '()
	 `(,(sprintf "  if (~A)~%" (intersperse (map (lambda (x) (sprintf "y.~A" x)) events) " || "))
	   ,(sprintf "    ~A_state.~A = 1e-4;~%" ivp-id hvar)
	   ,(sprintf "    y = ~A(~A_state);~%" ivp-id ivp-id)
	   ,(sprintf "  else~%")
	   ,(sprintf "    if (~A_state.~A < 0.25)~%" ivp-id hvar)
	   ,(sprintf "      ~A_state.~A = ~A_state.~A+1e-2;~%" ivp-id hvar ivp-id hvar)
	   ,(sprintf "    endif~%")
	   ,(sprintf "  endif~%")
	   ))

    ,(map (lambda (s) (sprintf "  ~A_state.~A = y.~A;~%" ivp-id s s)) states) 
    ,(sprintf "  data = [data; [~A]];~%" 
	      (string-concatenate (intersperse (map (lambda (s) (sprintf "y.~A" s)) states) ",") ))
    
    ,(sprintf "  t  = y.~A;~%" ivar )
    ,(sprintf "  i = i+1;~%")
    ,(sprintf "endwhile~%")
    ,(sprintf "toc;~%")

    ,(sprintf "save (\"-ascii\", ~S, \"data\");~%" log-path)
    )
  ))




(define (ivp-octave prefix ivp-id hvar ivar dvars pvars events start end ic sd)

  (let* (			
	 (N (+ 1 (length dvars)))
	 (P (- (length ic) N))
	 (dir        (or (pathname-directory prefix) "."))
	 (adir       (if (absolute-pathname? dir) dir
			 (make-pathname (current-directory) dir)))
	 (shared-dir         (chicken-home))
	 (solver-path        (make-pathname dir (sprintf "~A_solver.m" ivp-id)))
	 (m-path             (make-pathname dir (sprintf "~A_~A.m" (pathname-file prefix) ivp-id)))
	 (log-path           (make-pathname dir (sprintf "~A_~A.log" (pathname-file prefix) ivp-id)))
	 (octave-path        "octave")
	 )
    
    (make (
	   (solver-path (prefix)
			(with-output-to-file solver-path
			  (lambda () 
			    (codegen/Octave ivp-id sd solver: 'lsode))) )
	   
	   (m-path ()
		   (with-output-to-file m-path
		     (lambda () 
		       (print-fragments
			`(,(octave-m ivp-id start ivar hvar dvars events ic end log-path adir solver-path))))) )
	   
	   
	   (log-path (m-path solver-path)
		     (run (octave -q ,m-path)) )

#|	   
	   (clean ()
		  (run rm ,solver-path ,clib-path ,h-path
		       ,mlb-path ,clib-so-path ,lib-so-path
		       ,oct-cc-path ,oct-run-path ,oct-initial-path
		       ,oct-open-path ,oct-close-path ,m-path ,log-path))
|#
	   
	   )
      (list solver-path m-path log-path) )))

)

