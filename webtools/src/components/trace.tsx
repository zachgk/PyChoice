import {
  Box,
  Text,
  VStack,
  HStack,
  Badge,
  Code,
  TreeView,
  createTreeCollection
} from '@chakra-ui/react'
import type { TraceItemData } from './data';

interface TraceItemProps {
    item: TraceItemData;
    depth: number;
}

interface TreeNode {
  id: string;
  name: string;
  data: TraceItemData;
  children?: TreeNode[];
}

function TraceItem(props: TraceItemProps) {
    const {item, depth} = props;
    
    const convertToTreeNodes = (traceItem: TraceItemData, currentDepth: number = 0): TreeNode => {
      return {
        id: `${traceItem.func}-${currentDepth}-${Date.now()}`,
        name: traceItem.func,
        data: traceItem,
        children: traceItem.items.length > 0 
          ? traceItem.items.map((child, index) => convertToTreeNodes(child, currentDepth + 1))
          : undefined
      };
    };

    const renderTraceDetails = (traceItem: TraceItemData) => (
      <Box p={3} bg="gray.50" borderRadius="md" mt={2}>
        <VStack align="start" gap={2}>
          <HStack>
            <Text fontWeight="semibold">Implementation:</Text>
            <Code>{traceItem.impl}</Code>
          </HStack>
          
          <HStack>
            <Text fontWeight="semibold">Args:</Text>
            <Code>[{traceItem.args.join(', ')}]</Code>
          </HStack>
          
          {traceItem.rules.length > 0 && (
            <HStack>
              <Text fontWeight="semibold">Rules:</Text>
              <Code>[{JSON.stringify(traceItem.rules)}]</Code>
            </HStack>
          )}
          
          {Object.keys(traceItem.kwargs).length > 0 && (
            <HStack>
              <Text fontWeight="semibold">Kwargs:</Text>
              <Code>{JSON.stringify(traceItem.kwargs)}</Code>
            </HStack>
          )}
          
          {Object.keys(traceItem.choice_kwargs).length > 0 && (
            <HStack>
              <Text fontWeight="semibold">Choice Kwargs:</Text>
              <Code>{JSON.stringify(traceItem.choice_kwargs)}</Code>
            </HStack>
          )}
        </VStack>
      </Box>
    );

    const treeNode = convertToTreeNodes(item, depth);
    const collection = createTreeCollection<TreeNode>({
      nodeToValue: (node) => node.id,
      nodeToString: (node) => node.name,
      rootNode: {
        id: "ROOT",
        name: "",
        data: item,
        children: [treeNode],
      },
    });

    return (
      <TreeView.Root collection={collection} defaultExpandedValue={[treeNode.id]} mb={4}>
        <TreeView.Tree>
          <TreeView.Node<TreeNode>
            render={({ node, nodeState }) =>
              nodeState.isBranch ? (
                <TreeView.BranchControl>
                  <HStack>
                    <Badge colorScheme="blue" size="sm">Function</Badge>
                    <Text fontWeight="bold">{node.name}</Text>
                    {node.data && (
                      <Text fontSize="sm" color="gray.600">({node.data.impl})</Text>
                    )}
                    {node.children && node.children.length > 0 && (
                      <Badge colorScheme="gray" size="sm">
                        {node.children.length} nested
                      </Badge>
                    )}
                  </HStack>
                  {node.data && renderTraceDetails(node.data)}
                </TreeView.BranchControl>
              ) : (
                <TreeView.Item>
                  <HStack>
                    <Badge colorScheme="green" size="sm">Nested</Badge>
                    <Text fontWeight="bold">{node.name}</Text>
                    {node.data && (
                      <Text fontSize="sm" color="gray.600">({node.data.impl})</Text>
                    )}
                  </HStack>
                  {node.data && renderTraceDetails(node.data)}
                </TreeView.Item>
              )
            }
          />
        </TreeView.Tree>
      </TreeView.Root>
    );
}  

export default TraceItem
