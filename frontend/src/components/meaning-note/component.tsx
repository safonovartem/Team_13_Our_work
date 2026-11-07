import styles from './component.module.css';

interface MeaningNoteProps {
  children: string;
}

export function MeaningNote({ children }: MeaningNoteProps) {
  return <span className={styles.noteText}>{children}</span>;
}
