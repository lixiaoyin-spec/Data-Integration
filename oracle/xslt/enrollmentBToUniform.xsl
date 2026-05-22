<?xml version="1.0" encoding="UTF-8"?>
<!-- B(Oracle) 选课格式 → 统一集成格式 -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <Choices>
      <xsl:for-each select="enrollments/enrollment">
        <choice>
          <sid><xsl:value-of select="sid"/></sid>
          <cid><xsl:value-of select="cid"/></cid>
          <score/>
        </choice>
      </xsl:for-each>
    </Choices>
  </xsl:template>

</xsl:stylesheet>
