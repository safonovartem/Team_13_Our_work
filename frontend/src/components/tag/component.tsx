import styles from './component.module.css';

interface TagProps {
  children: string;
}

export function Tag({ children }: TagProps) {
  return <span className={styles.tag}>{children}</span>;
}
