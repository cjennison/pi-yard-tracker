import { createTheme } from '@mantine/core';
import type { MantineColorsTuple } from '@mantine/core';

// Custom wildlife/nature color palette
const forestGreen: MantineColorsTuple = [
  '#e7f5ee',
  '#d0e8dc',
  '#a1d1ba',
  '#6fb895',
  '#48a376',
  '#329661',
  '#268f56',
  '#1a7c47',
  '#0f6e3d',
  '#005f32',
];

const earthBrown: MantineColorsTuple = [
  '#fef4e6',
  '#f7e7cf',
  '#e9cda0',
  '#dcb26d',
  '#d09a42',
  '#c98b28',
  '#c6841b',
  '#af720f',
  '#9c6509',
  '#885600',
];

const skyBlue: MantineColorsTuple = [
  '#e5f4ff',
  '#cde2ff',
  '#9bc2ff',
  '#64a0ff',
  '#3984fe',
  '#1d72fe',
  '#0969ff',
  '#0058e4',
  '#004ecc',
  '#0043b5',
];

export const theme = createTheme({
  primaryColor: 'forestGreen',
  colors: {
    forestGreen,
    earthBrown,
    skyBlue,
  },
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  headings: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    fontWeight: '700',
  },
  defaultRadius: 'md',
  cursorType: 'pointer',
});
