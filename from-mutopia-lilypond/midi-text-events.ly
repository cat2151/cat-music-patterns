%% -dinclude-settings で読ませ、\midi 経路に届いた未対応記号を <出力名>.text-events.tsv へ書く。
%% 列: 時刻(全音符=1) / 先祖 context の id（, 区切り） / 種類 / 値

#(define (ancestor-ids ctx)
   (let loop ((c ctx) (acc '()))
     (if c
         (loop (ly:context-parent c)
               (let ((id (ly:context-id c)))
                 (if (member id '("" "\\new")) acc (cons id acc))))  ; "\new" は名前なし \new の id
         (string-join (reverse acc) ","))))

#(define (log-text-event translator kind value)
   (let* ((ctx (ly:translator-context translator))
          (p (open-file (string-append (ly:parser-output-name) ".text-events.tsv") "a")))
     (display (string-join
               (list (ly:format "~a" (exact->inexact (ly:moment-main (ly:context-current-moment ctx))))
                     (ancestor-ids ctx)
                     kind
                     (ly:format "~a" value))
               "\t")
              p)
     (newline p)
     (close p)))

%% 音になる・割り付け専用・別 performer で扱う event。これ以外は全部 text にする
#(define handled-classes
   '(note-event rest-event tie-event key-change-event
     skip-event bar-check-event bar-event line-break-event page-break-event
     beam-forbid-event reference-time-signature-event
     tempo-change-event))

#(define (handled? event class)
   (or (memq class handled-classes)
       ;; articulate がトリルを音符にした後に残る終了印
       (and (eq? class 'trill-span-event)
            (eqv? (ly:event-property event 'span-direction) STOP))))

#(define (event-value event)
   (let ((type (ly:event-property event 'articulation-type #f))
         (text (ly:event-property event 'text #f)))
     (cond (type type)
           ((markup? text) (markup->string text))
           (else ""))))

#(define text-events-performer
   (make-performer
    (listeners
     ((music-event performer event)
      (let ((class (car (ly:event-property event 'class))))
        (if (not (handled? event class))
            (log-text-event performer
                            (string-drop-right (symbol->string class) (string-length "-event"))
                            (event-value event))))))))

%% \tempo は Score に届くので、先祖 id は空になる
#(define tempo-text-performer
   (make-performer
    (listeners
     ((tempo-change-event performer event)
      (let ((text (ly:event-property event 'text #f)))
        (if text
            (log-text-event performer "tempo" (markup->string text))))))))

\midi {
  \context { \Voice \consists #text-events-performer }
  \context { \Score \consists #tempo-text-performer }
}
