import Papa from 'papaparse';

/**
 * Parse CSV string to array of objects
 */
export const parseCsv = <T = any>(csvText: string): T[] => {
  const result = Papa.parse<T>(csvText, {
    header: true,
    dynamicTyping: true,
    skipEmptyLines: true,
  });

  if (result.errors.length > 0) {
    console.error('CSV parsing errors:', result.errors);
  }

  return result.data;
};

/**
 * Parse CSV file from URL
 */
export const parseCsvFromUrl = async <T = any>(url: string): Promise<T[]> => {
  try {
    const response = await fetch(url);
    const csvText = await response.text();
    return parseCsv<T>(csvText);
  } catch (error) {
    console.error('Error loading CSV:', error);
    throw error;
  }
};
