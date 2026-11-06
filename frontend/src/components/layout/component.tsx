import { ReactNode } from 'react';

import styles from './component.module.css';

interface LayoutProps {
  header: ReactNode;
  aside?: ReactNode;
  children?: ReactNode;
}

export function Layout({ header, aside, children }: LayoutProps) {
  return (
    <div className={aside ? styles.layout : styles.layoutNoAside}>
      <header className={styles.headerArea}>{header}</header>
      {aside && <aside className={styles.asideArea}>{aside}</aside>}
      <main className={styles.mainArea}>{children}</main>
    </div>
  );
}
