// Pure helpers for CardRow.astro, kept here so they can be tested without a
// browser. The component's script reads the sizes from the page and calls these.

export interface ArrowState {
  /** The row is wider than the view, so the arrows are worth showing. */
  show: boolean;
  /** Scrolled all the way left: the left arrow does nothing. */
  atStart: boolean;
  /** Scrolled all the way right: the right arrow does nothing. */
  atEnd: boolean;
}

// Browsers report fractional scroll positions, so allow a pixel of slack.
const SLACK = 1;

export function arrowState(scrollLeft: number, scrollWidth: number, clientWidth: number): ArrowState {
  const max = scrollWidth - clientWidth;
  return {
    show: max > SLACK,
    atStart: scrollLeft <= SLACK,
    atEnd: scrollLeft >= max - SLACK,
  };
}

/**
 * How far one arrow press scrolls: as many whole cards as fit in the view, at
 * least one, so the next press starts on a card edge.
 */
export function scrollStep(viewWidth: number, cardWidth: number, gap: number): number {
  const stride = cardWidth + gap;
  if (stride <= 0) return viewWidth;
  const perView = Math.max(1, Math.floor((viewWidth + gap) / stride));
  return perView * stride;
}
