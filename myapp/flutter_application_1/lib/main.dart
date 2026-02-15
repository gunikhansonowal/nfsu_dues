import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: DashboardScreen(),
    );
  }
}

//DASHBOARD SCREEN
class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int currentPage = 1;

  List<Map<String, String>> tableData = [
    {"caseid": "01", "originalsize": "4GB", "compressedsize": "1GB", "spacesaved": "25%"},
    {"caseid": "02", "originalsize": "7GB", "compressedsize": "2GB", "spacesaved": "28.57%"},
    {"caseid": "03", "originalsize": "65GB", "compressedsize": "20GB", "spacesaved": "30.77%"},
    {"caseid": "04", "originalsize": "20GB", "compressedsize": "6GB", "spacesaved": "30%"},
    {"caseid": "05", "originalsize": "38GB", "compressedsize": "10GB", "spacesaved": "26.31%"},
    {"caseid": "06", "originalsize": "40GB", "compressedsize": "12GB", "spacesaved": "30%"},
    {"caseid": "07", "originalsize": "15GB", "compressedsize": "4GB", "spacesaved": "26.67%"},
    {"caseid": "08", "originalsize": "70GB", "compressedsize": "30GB", "spacesaved": "42.86%"},
    {"caseid": "09", "originalsize": "10GB", "compressedsize": "4GB", "spacesaved": "40%"},
    {"caseid": "10", "originalsize": "65GB", "compressedsize": "20GB", "spacesaved": "30.77%"},
  ];

  double _parseGB(String v) =>
      double.tryParse(v.replaceAll("GB", "")) ?? 0;

  double totalOriginal() =>
      tableData.fold(0, (s, e) => s + _parseGB(e['originalsize']!));

  double totalCompressed() =>
      tableData.fold(0, (s, e) => s + _parseGB(e['compressedsize']!));

  double totalReduced() => totalOriginal() - totalCompressed();

  Color rowColor(int i) =>
      i.isEven ? Colors.green.shade50 : Colors.grey.shade100;

  //EDIT ROW
  void _editRow(int index) {
    final o = TextEditingController(text: tableData[index]['originalsize']);
    final c = TextEditingController(text: tableData[index]['compressedsize']);
    final s = TextEditingController(text: tableData[index]['spacesaved']);

    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text("Edit Case"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: o, decoration: const InputDecoration(labelText: "Original Size")),
            TextField(controller: c, decoration: const InputDecoration(labelText: "Compressed Size")),
            TextField(controller: s, decoration: const InputDecoration(labelText: "Space Saved")),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("Cancel")),
          ElevatedButton(
            onPressed: () {
              setState(() {
                tableData[index]['originalsize'] = o.text;
                tableData[index]['compressedsize'] = c.text;
                tableData[index]['spacesaved'] = s.text;
              });
              Navigator.pop(context);
            },
            child: const Text("Save"),
          ),
        ],
      ),
    );
  }

  DataCell editableCell(String v, int i) =>
      DataCell(Text(v), onTap: () => _editRow(i));

  //PIE CHART
  List<PieChartSectionData> pieSections() => [
        PieChartSectionData(
          value: totalCompressed(),
          title: "Compressed",
          color: Colors.blue,
          radius: 60,
        ),
        PieChartSectionData(
          value: totalReduced(),
          title: "Reduced",
          color: Colors.green,
          radius: 60,
        ),
      ];

  //UI
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Dashboard")),

      //SIDE MENU 
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            DrawerHeader(
              decoration: const BoxDecoration(color: Colors.indigo),
              child: Row(
                children: const [
                  Icon(Icons.dashboard, color: Colors.white, size: 40),
                  SizedBox(width: 12),
                  Text("My Dashboard",
                      style: TextStyle(color: Colors.white, fontSize: 20)),
                ],
              ),
            ),
            ListTile(
              leading: const Icon(Icons.dashboard),
              title: const Text("Dashboard"),
              onTap: () => Navigator.pop(context),
            ),
            ExpansionTile(
              leading: const Icon(Icons.folder),
              title: const Text("Case Management"),
              children: const [
                ListTile(leading: Icon(Icons.add), title: Text("Add Case")),
                ListTile(leading: Icon(Icons.list), title: Text("View Cases")),
              ],
            ),
          ],
        ),
      ),

      //BODY 
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [

            const Spacer(flex: 3),

            Expanded(
              flex: 7,
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 800),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: DataTable(
                          headingRowColor:
                              MaterialStateProperty.all(Colors.indigo.shade100),
                          columns: const [
                            DataColumn(label: Text("Case ID")),
                            DataColumn(label: Text("Original Size")),
                            DataColumn(label: Text("Compressed Size")),
                            DataColumn(label: Text("Space Saved")),
                          ],
                          rows: List.generate(
                            tableData.length,
                            (i) => DataRow(
                              color: MaterialStateProperty.all(rowColor(i)),
                              cells: [
                                DataCell(Text(tableData[i]['caseid']!)),
                                editableCell(tableData[i]['originalsize']!, i),
                                editableCell(tableData[i]['compressedsize']!, i),
                                editableCell(tableData[i]['spacesaved']!, i),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          TextButton(
                            onPressed: currentPage > 1
                                ? () => setState(() => currentPage--)
                                : null,
                            child: const Text("Prev"),
                          ),
                          Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 12),
                            child: Text("Page $currentPage",
                                style: const TextStyle(fontWeight: FontWeight.bold)),
                          ),
                          TextButton(
                            onPressed: () => setState(() => currentPage++),
                            child: const Text("Next"),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),

            const SizedBox(width: 30),

            //RIGHT PIE CHART
            Expanded(
              flex: 3,
              child: Column(
                children: [
                  const Text(
                    "Overall Size Reduction",
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    height: 260,
                    child: PieChart(
                      PieChartData(
                        sections: pieSections(),
                        centerSpaceRadius: 40,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    "Original: ${totalOriginal()} GB\nCompressed: ${totalCompressed()} GB",
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
