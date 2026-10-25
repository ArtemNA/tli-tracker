import { Component, computed, inject } from '@angular/core';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { DurationPipe, FePipe } from '../core/format';
import { TranslatePipe } from '../core/i18n';
import { TrackerStore } from '../core/tracker.store';
import { MapLabelPipe } from '../ui/map-label.pipe';

/** Small always-on-top window shown over the game. */
@Component({
  selector: 'app-overlay',
  imports: [FePipe, DurationPipe, TranslatePipe, MapLabelPipe],
  template: `
    @if (store.snapshot(); as s) {
      <div class="overlay" [style.--alpha]="s.settings.overlayOpacity" data-tauri-drag-region>
        <div class="top" data-tauri-drag-region>
          <span class="dot" [class.live]="s.status === 'active'"></span>
          <span class="map" data-tauri-drag-region>{{ s.current ? (s.current | mapLabel) : ('current.none' | t) }}</span>
          <button type="button" class="x" (click)="close()" [title]="'common.close' | t">×</button>
        </div>
        <div class="main" data-tauri-drag-region>
          <div><small>{{ 'runs.time' | t }}</small><b class="num">{{ store.currentDurationMs() | duration }}</b></div>
          <div><small>{{ 'runs.profit' | t }}</small><b class="num" [class.neg]="(s.current?.profit ?? 0) < 0">{{ s.current?.profit ?? 0 | fe: true }}</b></div>
        </div>
        <div class="foot" data-tauri-drag-region>
          <span>{{ 'overlay.session' | t }} <b class="num fe">{{ s.session.profit | fe: true }}</b></span>
          <span><b class="num">{{ perHour() | fe }}</b>/h</span>
          <span><b class="num">{{ s.session.mapCount }}</b> {{ 'analytics.mapsShort' | t }}</span>
        </div>
      </div>
    }
  `,
  styles: `
    :host { display: block; height: 100vh; }
    .overlay {
      height: 100%;
      display: flex; flex-direction: column; justify-content: space-between;
      padding: 10px 12px;
      background: rgb(16 15 18 / var(--alpha, .92));
      color: #f3f1ee;
      border: 1px solid rgb(255 255 255 / 8%);
      border-radius: 10px;
      user-select: none;
      cursor: move;
    }
    .top { display: flex; align-items: center; gap: 8px; }
    .map { flex: 1; font-size: 12px; color: #c9c4bd; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: #6b6670; }
    .dot.live { background: #3ecf8e; }
    .x { border: 0; background: none; color: #8d8790; font-size: 18px; line-height: 1; cursor: pointer; padding: 0 2px; }
    .x:hover { color: #fff; }
    .main { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .main div { display: flex; flex-direction: column; }
    small { font-size: 10px; text-transform: uppercase; letter-spacing: .08em; color: #8d8790; }
    .main b { font-size: 24px; font-weight: 650; }
    .foot { display: flex; justify-content: space-between; font-size: 12px; color: #a59f98; }
    .foot b { color: #f3f1ee; }
    .fe { color: #f5c35b !important; }
    .neg { color: #ff6b6b; }
  `,
})
export class Overlay {
  readonly store = inject(TrackerStore);
  readonly perHour = computed(() => {
    const s = this.store.snapshot();
    const ms = this.store.sessionMapTimeMs();
    return s && ms > 0 ? s.session.profit / (ms / 3_600_000) : 0;
  });

  close(): void {
    void getCurrentWindow().close();
  }
}
